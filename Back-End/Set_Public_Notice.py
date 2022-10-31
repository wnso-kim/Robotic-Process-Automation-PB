import requests
import zipfile
import xmltodict
import json
import time
import pandas as pd
from io import BytesIO
from Base import DB, DartKey
from datetime import datetime, timedelta


#--------------------------------------------------------------------------
# Dart 클래스
class Dart() :
    def __init__(self):
        self.api_key = DartKey().GetApiKey()
        self.url = ''
        self.datetime = datetime.now()

        # prameter
        self.params = {
            'crtfc_key' : self.api_key, # API 인증키
            'corp_code' : '',           # 고유번호
            'bgn_de' : '',              # 시작일
            'end_de' : '',              # 종료일
            'page_count' : '10',          # 페이지 별 건수(10~50)
        }

        # DB 연결
        self.db = DB()
        self.cursor = self.db.GetCursor()

#--------------------------------------------------------------------------
    # 종목 고유번호를 DB에 저장하는 함수
    # DB kospi_code.code | column corp_code에 저장
    def SetCorpCode(self):
        # request url 연결
        self.url ='https://opendart.fss.or.kr/api/corpCode.xml'
        # request
        res = requests.get(self.url, self.params)
        data_xml = zipfile.ZipFile(BytesIO(res.content))
        data_xml.namelist()
        
        # xml -> dict 변환
        data_xml = data_xml.read('CORPCODE.xml').decode('utf-8')
        data_odict = xmltodict.parse(data_xml)
        data_dict = json.loads(json.dumps(data_odict))
        data = data_dict.get('result', {}).get('list')
        
        # time sleep -> CPU충돌방지
        time.sleep(0.1)
        # dic에 종목코드(key) : 고유번호(value)로 저장
        dic = {}
        for item in data:
            dic[item['stock_code']] = item['corp_code']
        
        # time sleep -> CPU충돌방지
        time.sleep(0.1)
        # DB kospi_code.code의 name, stock_code 컬럼 받아오기
        self.cursor.execute('use kospi_code')
        self.cursor.execute('select name,stock_code from code;')
        result = self.cursor.fetchall()

        # dlist 추가
        # Dart와 Kis의 종목코드(stock_code)가 같은경우
        # dlist에 {종목이름, 종목코드, 고유번호} 저장
        dlist = []
        for item in result:
            try:
                dlist.append({'name':item['name'], 'stock_code':item['stock_code'], 'corp_code':dic[item['stock_code']]})
            except:
                pass

        # row 값 추가를 위한 insert string
        # data insert
        # name(종목이름), stock_code(종목코드), corp_code(고유번호) insert
        insert = f"insert into `code` (name,stock_code,corp_code) values (%(name)s, %(stock_code)s, %(corp_code)s) as new on duplicate key update corp_code = new.corp_code;"
        self.cursor.executemany(insert, dlist)

        # data dalete -> copr_code==Null 경우
        delete = f"delete from `code` where `corp_code` is NULL;"
        self.cursor.execute(delete)

        # DB커밋
        self.db.Commit()
        


#--------------------------------------------------------------------------
    # 공시제목, PDF_URL을 DB에 저장하는 함수 -> 오늘부터 day 만큼 읽어와 저장 
    # dart_api.public_notice | datetime, title, name, pdf_url에 저장
    def SetPublicNotice(self, result, day):
        self.datetime = datetime.now()
        
        dlist = []
        for item in result:
            # request url 연결
            self.url = 'https://opendart.fss.or.kr/api/list.json'
            # parameter 고유번호/시작일/종료일/건수 수정
            self.params['corp_code'] = item['corp_code']
            self.params['end_de'] = self.datetime.strftime('%Y%m%d')  # 종료일 : 오늘  
            self.params['bgn_de'] = (self.datetime - timedelta(days=day)).strftime('%Y%m%d') # 시작일 : day일 전
            if day>=50 : # 50일 정보를 읽는 경우
                self.params['page_count'] = 100 # 페이지 건수 최대
            else :
                self.params['page_count'] = 10  # 페이지 건수 10회

            # request
            res = requests.get(self.url, self.params)
            data = res.json()

            # request로 얻은 데이터를 pandas DataFrame으로 변환
            data_list = data.get('list')
            df_list = pd.DataFrame(data_list)
        
            # dlist에 datetime, title, name, rcept_no, pdf_url추가
            # df_list index
            # corp_code[1] corp_name[2] stock_code[3] corp_cls[4] report_nm[5]
            # rcept_no[6] flr_nm[7] rcept_dt[8] rm[9]
            pdf_url = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='
            for row in df_list.itertuples():
                dlist.append({'datetime':row[8], 'title':row[5], 'name':row[2], 'rcept_no':row[6], 'pdf_url':pdf_url+row[6]})
        
        # row 값 추가를 위한 insert string
        # data insert
        # datetime(날짜), title(보고서명), name(종목이름), rcept_no(접수번호) insert
        insert = f"insert ignore into `public_notice` (datetime,title,name,pdf_url,rcept_no) values (%(datetime)s,%(title)s,%(name)s,%(pdf_url)s,%(rcept_no)s);"
        self.cursor.execute('use dart_api')
        self.cursor.executemany(insert, dlist)

        # DB커밋
        self.db.Commit()
        print('SetPublicNotice',datetime.now()-self.datetime)






