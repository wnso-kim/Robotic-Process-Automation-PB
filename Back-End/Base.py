import requests
import json
import pymysql
from datetime import datetime 

#--------------------------------------------------------------------------
# AccessToken 클래스
class AccessToken :
    def __init__(self):
        self.starttime = datetime.now()
        self.APP_KEY = "PSjTTTMhFyHdsLFfJm2CzSGMbLkBEF8nLKJW"
        self.APP_SECRET = "PV+kbdrXdtuzA2IZmlmNRcmTeFFrX36c2R/nIA1k1ycKYFoNfos04y4wkeucqiOGAaOMWMnxvX/XQ1+Syd04d4mWPWSId7lJbX30YOTWN3NXUmouR4kAXwaBC42VhC+2TOIjQIcpRG7wAx9eUn+PS5Nb3LQrS4FMdOfjbOTQZ95ZC48SnD0="
        self.URL_BASE = "https://openapi.koreainvestment.com:9443" # 실전투자서비스

        self.headers = {"content-type":"application/json",
                        # 조회를 위한 header request
                        "authorization":"",
                        "appKey":"",
                        "appSecret":"",
                        "tr_id":""
                        }
        self.body = {"grant_type":"client_credentials",
                    "appkey":self.APP_KEY, 
                    "appsecret":self.APP_SECRET}

        self.PATH = "oauth2/tokenP"
        self.URL = f"{self.URL_BASE}/{self.PATH}" 


    def GetAccessToken(self):
        self.res = requests.post(self.URL, headers=self.headers, data=json.dumps(self.body))
        self.ACCESS_TOKEN = self.res.json()["access_token"]
        return self.ACCESS_TOKEN

#--------------------------------------------------------------------------
# DB 클래스
class DB :
    def __init__(self):
        self.db = pymysql.connect(
            # host='localhost' 가능
            host='3.39.234.81', user='wc', 
            password='root', port=3306, charset='utf8')

    def GetCursor(self):
        # DB cursor 반환
        return self.db.cursor(pymysql.cursors.DictCursor)   

    def GetKospiCode(self):
        cursor = self.GetCursor()
        cursor.execute('select * from kospi_code.code;')
        result = cursor.fetchall()
        return result

    def Commit(self):
        self.db.commit()

    def Close(self):
        self.db.close()

    
#--------------------------------------------------------------------------
# DartKey 클래스
class DartKey :
    def __init__(self):
        self.api_key='6b077755950e89e2c8d1f705ee531c0374cd1da8'
    
    def GetApiKey(self):
        return self.api_key
