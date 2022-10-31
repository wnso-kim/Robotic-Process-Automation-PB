import requests
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
from Base import DB

# 웹 크롤러를 위한 Crawler class
class Crawler:
#--------------------------------------------------------------------------
    # 초기화 함수
    def __init__(self):
        self.date = datetime.now()          # 현재 시간 저장
        self.query = ""                     # 검색할 종목 이름
        self.url = ""                       # NEWS_URL | RESEARCH_URL
        self.req = None                     # requests.get() 반환값을 받을 변수
        self.soup = None                    # BeautifulSoup 파싱 반환값을 받을 변수
        self.db = DB()                      # DB 객체 생성
        self.cursor = self.db.GetCursor()   # DB 커서 생성
#--------------------------------------------------------------------------
    # News 크롤러를 위한 함수  
    # 종목별 네이버 뉴스 검색
    def News(self, list, pd):                     # list = 종목이름 | 종목코드 | 고유번호
        self.date = datetime.now()
        dlist = []                    
        for item in list:
            self.query = item['name'].replace(' ', '+')  # name에 띄어쓰기가 있는경우 +로 연결
            # 네이버뉴스 | 최신순 | 1시간[pd=7] <-> 1일간[pd=4]
            self.url = f'https://search.naver.com/search.naver?where=news&query={self.query}&sm=tab_opt&sort=1&photo=0&field=0&pd={pd}&ds=&de=&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Add%2Cp%3A1d&is_sug_officeid=0'
            self.req = requests.get(self.url)                        # Request HTTP 요청 -> HTML응답
            self.soup = BeautifulSoup(self.req.text, 'html.parser')  # HTML 파싱
            # title | press | time 데이터 얻음
            title = self.soup.find_all('a','news_tit')   # 기사 제목 | 링크
            press = self.soup.find_all('a','info press') # 언론사 
            time = self.soup.find_all('span','info')     # 기사 시간
            
            # 얻은 데이터 -> dlist에 저장
            idx = 0 # time[i] 시간 데이터가 아닌 경우 제외``
            for i in range(min(len(title),10)): 
                try:
                    title_ = title[i].get_text()                                # title 저장
                    url_ = title[i].get('href')                                 # url 저장
                    press_ = press[i].get_text(separator=" ").split(" ")[0]     # press 저장 -> 언론사 선정 text 제외
                except:
                    continue

                # time 저장
                if not time[i+idx].get_text().endswith('전'): idx += 1      # 시간 데이터가 아닌 경우 넘김
                time_ = time[i+idx].get_text(separator=" ").split(" ")[-2]  # 시간
                try: # ex) 2분 전 -> 2
                    time_ = int(time_[:time_.find('분')])
                    time_ = (datetime.now() - timedelta(minutes=time_)).strftime('%y-%m-%d %H:%M:%S')
                except: # ex) 1시간 전 -> 1
                    time_ = int(time_[:time_.find('시')])
                    time_ = (datetime.now() - timedelta(hours=time_)).strftime('%y-%m-%d %H:%M:%S')
                    
                # dlist에 저장
                dlist.append({'datetime': time_, 'title' : title_, 'press': press_, 'name':self.query, 'url' : url_ })

        # DB news_research.news에 저장
        insert = f'insert ignore into news_research.news (datetime, title, press, name, url) values (%(datetime)s, %(title)s, %(press)s, %(name)s, %(url)s);'
        self.cursor.executemany(insert, dlist)
        self.db.Commit()

        print('News', datetime.now() - self.date)   #코드 종료 시각

#--------------------------------------------------------------------------
    # Research 크롤러를 위한 함수 
    # 시황정보 | 투자정보 | 경제분석 | 채권분석
    def Research_1(self):
        self.date = datetime.now()
        date_ = self.date.strftime('%Y-%m-%d')
        url = [
            # 시황정보 | 투자정보 | 경제분석 | 채권분석 url
            f'https://finance.naver.com/research/market_info_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}',
            f'https://finance.naver.com/research/invest_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}',
            f'https://finance.naver.com/research/economy_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}',
            f'https://finance.naver.com/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}'
        ]

        dlist = []                                                          # 데이터 푸시를 위한 딕셔너리 리스트
        for idx in range(4):
            # URL 설정    
            self.url = url[idx]  
            self.req = requests.get(self.url)                               # HTTP 요청 -> HTML응답
            self.soup = BeautifulSoup(self.req.text, 'html.parser')         # HTML 파싱

            # title | company | pdf_url
            try:
                table = self.soup.find('table', class_='type_1')            # table
                title_company = table.find_all('td',class_=None)            # title | company
                pdf_url = table.find_all('a', target='_blank')              # pdf_url
            except:
                continue

            # dlist append
            for i in range(len(pdf_url)) :
                title_ = title_company[i*2].get_text()                      # title
                company_ = title_company[i*2+1].get_text()                  # company
                pdf_url_ = pdf_url[i].get('href')                           # pdf_url
                # append
                dlist.append({'datetime':datetime.now(), 'title':title_, 'company':company_, 'pdf_url':pdf_url_})     
            
        # DB news_research.news에 저장
        insert = f'insert ignore into news_research.research (datetime, title, company, name, pdf_url) values (%(datetime)s, %(title)s, %(company)s, Null, %(pdf_url)s);'
        self.cursor.executemany(insert, dlist)
        self.db.Commit()

        print('Research_1   ', datetime.now() - self.date)
#--------------------------------------------------------------------------   
    # Research 크롤러를 위한 함수  
    # 종목분석
    def Research_2(self):    
        self.date = datetime.now()
        date_ = self.date.strftime('%Y-%m-%d')

        dlist = []                                                          # 데이터 푸시를 위한 딕셔너리 리스트        
        # URL 설정(종목분석 리서치)      
        self.url = f'https://finance.naver.com/research/company_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}' 
        self.req = requests.get(self.url)                                   # HTTP 요청 -> HTML응답
        self.soup = BeautifulSoup(self.req.text, 'html.parser')             # HTML 파싱

        # title | company | name | pdf_url
        try:
            table = self.soup.find('table', class_='type_1')                # table
            title_company = table.find_all('td',class_=None)                # title | company
            name = table.find_all('a', class_='stock_item')                 # name
            pdf_url = table.find_all('a', target='_blank')                  # pdf_url
        except:
            return

        # dlist append
        for i in range(len(pdf_url)) :
            title_ = title_company[i*3+1].get_text()                        # title
            company_ = title_company[i*3+2].get_text()                      # company
            name_ = name[i].get('title')                                    # name
            pdf_url_ = pdf_url[i].get('href')                               # pdf_url
            # append
            dlist.append({'datetime':datetime.now(), 'title':title_, 'company':company_, 'name':name_, 'pdf_url':pdf_url_})     
            
        # DB news_research.news에 저장
        insert = f'insert ignore into news_research.research (datetime, title, company, name, pdf_url) values (%(datetime)s, %(title)s, %(company)s, %(name)s, %(pdf_url)s);'
        self.cursor.executemany(insert, dlist)
        self.db.Commit()

        print('Research_2   ', datetime.now() - self.date)

#--------------------------------------------------------------------------   
    # Research 크롤러를 위한 함수  
    # 산업분석
    def Research_3(self):                  
        self.date = datetime.now()
        date_ = self.date.strftime('%Y-%m-%d')

        dlist = []                                                          # 데이터 푸시를 위한 딕셔너리 리스트
        # URL 설정(산업분석 리서치)      
        self.url = f'https://finance.naver.com/research/industry_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={date_}&writeToDate={date_}' 
        self.req = requests.get(self.url)                                   # HTTP 요청 -> HTML응답
        self.soup = BeautifulSoup(self.req.text, 'html.parser')             # HTML 파싱

        # title | company | pdf_url
        try:
            table = self.soup.find('table', class_='type_1')                # table
            title_company = table.find_all('td',class_=None)                # title | company
            pdf_url = table.find_all('a', target='_blank')                  # pdf_url
        except:
            return      
        
        # dlist append
        for i in range(len(pdf_url)) :
            title_ = title_company[i*3+1].get_text()                        # title
            company_ = title_company[i*3+2].get_text()                      # company
            pdf_url_ = pdf_url[i].get('href')                               # pdf_url
            # append
            dlist.append({'datetime':datetime.now(), 'title':title_, 'company':company_, 'pdf_url':pdf_url_})     
            
        # DB news_research.news에 저장
        insert = f'insert ignore into news_research.research (datetime, title, company, name, pdf_url) values (%(datetime)s, %(title)s, %(company)s, Null, %(pdf_url)s);'
        self.cursor.executemany(insert, dlist)
        self.db.Commit()

        print('Research_3   ', datetime.now() - self.date)

