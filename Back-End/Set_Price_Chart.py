import requests
from Base import AccessToken, DB
from datetime import datetime, timedelta


#--------------------------------------------------------------------------
# 차트를 얻기위한 클래스
class PriceChart(AccessToken) :
    def __init__(self) :
        # Access token 발급
        self.at = AccessToken()
        self.AT = self.at.GetAccessToken()

        # headers 리스트 추가
        self.at.headers["authorization"] = f"Bearer {self.AT}"
        self.at.headers["appKey"] = self.at.APP_KEY
        self.at.headers["appSecret"] = self.at.APP_SECRET
        self.at.headers["tr_id"] = "" #거래ID

        # Query Parameter Day -> 당일분봉조회 사용
        self.params_day = {
                "fid_etc_cls_code": "",
                "fid_cond_mrkt_div_code":"J",
                "fid_input_hour_1": "",     # 조회시작일자
                "fid_input_iscd":"",        # 종목번호
                "fid_pw_data_incu_yn": "Y"
        }

        # Query Parameter Month -> 월봉조회 사용
        self.params_month = {
                "fid_cond_mrkt_div_code":"J",
                "fid_input_date_1": "",     # 조회시작일자
                "fid_input_date_2":"",      # 조회종료일자
                "fid_input_iscd":"",        # 종목번호
                "fid_period_div_code": "M", # 기간분류코드(월봉)
                "fid_org_adj_prc" : "0"     # 수정주가
        }

        # Query Parameter Price -> 현재시세조회 사용
        self.params_price = {
                "fid_cond_mrkt_div_code":"J",
                "fid_input_iscd":"",  #종목번호
        }

        # DB 객체 생성
        self.db = DB()
        self.cursor = self.db.GetCursor()

#--------------------------------------------------------------------------
    # 당일분봉조회 및 DB작업 함수
    # 국내주식시세_주식당일분봉조회 사용
    def SetDayChart(self, result) :
        st = datetime.now()

        self.at.starttime = datetime.now()
        # headers 리스트 수정
        self.at.headers["tr_id"] = "FHKST03010200" # 주식당일분봉조회
        for item in result:
            stock_code = item['stock_code']
            stock_name = item['name']
            # Query Parameter Day 수정
            self.params_day['fid_input_iscd'] = stock_code # 종목번호

            # URL 지정
            self.PATH = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
            self.URL = f"{self.at.URL_BASE}/{self.PATH}"

            # 현재 시간 변수 -> Query Parameter 조회시작일자에 필요
            time = self.datetime_to_time()
            if time<'090000':
                time = '153000'
                # 새벽인 경우 전 날로 바꿔줌
                self.at.starttime = datetime.now() - timedelta(days=1)
            elif '153000'<time: 
                time = '153000'       
            
            # 분봉시세 조회 -> dict에 저장
            # 현재시간부터 오전9시까지 분봉시세 조회
            dlist = []          # DB에 넣기위한 dictionary list
            check = True        # 예외처리를 위한 bool
            while check:
                self.params_day["fid_input_hour_1"] = time # 조회시작일자 수정

                # 현재시간(최대:15:30:00)부터 오전 9시까지 분봉시세를 조회함
                # REST API : 1초 10회 조회가능 -> output못찾는 경우 예외처리로 반복
                while True:
                    try:
                        res = requests.get(self.URL, headers=self.at.headers, params=self.params_day)
                        for i in res.json()["output2"]:
                            self.dt = self.time_to_datetime(i['stck_cntg_hour']) #datetime 변수 생성
                            dlist.append({'datetime':self.dt, stock_name:int(i['stck_prpr'])})
                            
                            time = i['stck_cntg_hour']
                            if time=='090000': 
                                check = False
                                break
                    except:
                        continue

                    break
            
            # DB 삽입
            # column 추가를 위한 add string 
            # column 값 추가를 위한 insert string
            
            add = f"alter table `price` add `{stock_name}` integer;"
            insert = f"insert into `price` (datetime,`{stock_name}`) values (%(datetime)s, %({stock_name})s) as new on duplicate key update `{stock_name}` = new.`{stock_name}`;"

            # Table 선택 
            self.cursor.execute('use kis_api')
            try:
                self.cursor.execute(add)
            except: 
                pass
            # column 추가
            self.cursor.executemany(insert, dlist)
        # DB커밋
        self.db.Commit()

        # print
        print('SetDayChart', datetime.now()-st)

#--------------------------------------------------------------------------
    # 월봉조회 및 DB작업 함수
    # 국내주식시세_국내주식기간별시세(일/주/월/년) 사용
    def SetMonthChart(self, result) :
        st = datetime.now()

        # URL 지정
        self.PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        self.URL = f"{self.at.URL_BASE}/{self.PATH}"

        # headers 리스트 수정
        self.at.headers["tr_id"] = "FHKST03010100 " # 국내주식기간별시세

        for item in result:
            stock_code = item['stock_code']
            stock_name = item['name']

            # 오늘부터 5년간
            date_s = (datetime.now() - timedelta(days=1825)).strftime('%Y%m%d')
            date_e = datetime.now().strftime('%Y%m%d')
            date_t = datetime.now() - timedelta(days=1825)         # 예외처리를 위한 date_t
            delta_t = timedelta(days=30)                           # 예외처리를 위한 delta_t

            # Query Parameter 수정
            self.params_month["fid_input_iscd"] = stock_code # 종목번호
            self.params_month["fid_input_date_1"] = date_s # 조회시작일자 수정
            self.params_month["fid_input_date_2"] = date_e # 조회종료일자 수정

            # 월봉시세 조회 -> dict에 저장
            # 오늘부터 5년간의 월봉 조회
            dlist = []          # DB에 넣기위한 dictionary list
            # 예외 발생시 반복
            while True:
                try:
                    res = requests.get(self.URL, headers=self.at.headers, params=self.params_month)
                    for i in res.json()["output2"]:
                        dlist.append({'date':i['stck_bsop_date'], stock_name:int(i['stck_clpr'])})
                    break

                except :
                    # 조회시작일자 한달 뒤로 수정
                    date_t = date_t + delta_t
                    self.params_month["fid_input_date_1"] = date_t.strftime('%Y%m%d') 

            print(stock_name)
            # DB 삽입
            # column 추가를 위한 add string 
            # column 값 추가를 위한 insert string
            add = f"alter table `price_month` add `{stock_name}` integer;"
            insert = f"insert into `price_month` (date,`{stock_name}`) values (%(date)s, %({stock_name})s) as new on duplicate key update `{stock_name}` = new.`{stock_name}`;"
            # Table 선택 
            self.cursor.execute('use kis_api')
            try:
                self.cursor.execute(add)
            except: 
                pass
            # column 추가
            self.cursor.executemany(insert, dlist)
            
        # DB커밋
        self.db.Commit()
        # print
        print('SetMonthChart', datetime.now()-st)

#--------------------------------------------------------------------------
    # 현재시세조회 및 DB작업 함수
    # 국내주식시세_주식현재가 시세 사용
    def SetPriceChart(self, result) :
        st = datetime.now()

        for item in result:
            stock_code = item['stock_code']
            stock_name = item['name']
            # 장외 시간인지 확인
            # 장외 시간인 경우 함수 종료
            time = datetime.now().strftime('%H:%M:00')
            if(time<'09:00:00' or '15:31:00'<=time): continue 

            # headers 리스트 수정
            self.at.headers["tr_id"] = "FHKST01010100 " # 주식현재가 시세

            # Query Parameter 수정
            self.params_price = {"fid_cond_mrkt_div_code": "J",
                            "fid_input_iscd": stock_code # 종목번호
            }

            # URL 지정
            self.PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
            self.URL = f"{self.at.URL_BASE}/{self.PATH}"

            # 현재시세조회
            # REST API : 1초 20회 조회가능 -> output 못찾는 경우가 발생해 예외처리로 반복
            dict_ = {}
            while True:
                try:
                    # 현재 시간 설정
                    self.at.starttime = datetime.now()
                    # request
                    res = requests.get(self.URL, headers=self.at.headers, params=self.params_price)
                    dict_['datetime'] = self.at.starttime.strftime('%Y-%m-%d %H:%M:00')
                    dict_[stock_name] = int(res.json()['output']['stck_prpr'])
                except:
                    continue

                break

            # DB 삽입
            # column 값 추가를 위한 insert string
            insert = f"insert into `price` (datetime,`{stock_name}`) values (%(datetime)s, %({stock_name})s) as new on duplicate key update `{stock_name}` = new.`{stock_name}`;"
            
            # Table 선택 및 column 추가
            self.cursor.execute('use kis_api')
            self.cursor.execute(insert, dict_)

        # DB커밋
        self.db.Commit()

        # print
        print('SetPriceChart', datetime.now()-st)
        
#-------------------------------------------------------------------------
    # 기타 함수

    # 날짜를 시간으로 바꾸는 함수
    # YYYY-MM-DD HH:MM:SS -> HHMMSS
    def datetime_to_time(self):
        return str(self.at.starttime.strftime('%H%M%S'))


    # 시간을 날짜로 바꾸는 함수
    # HHMMSS -> YYYY-MM-DD HH:MM:SS
    def time_to_datetime(self, HHMMSS):
        return str(self.at.starttime.strftime('%Y-%m-%d ') + HHMMSS[:2] + ':' + HHMMSS[2:4] + ':' + HHMMSS[4:6])
     
