import requests
import json
import pymysql
from datetime import datetime 

#--------------------------------------------------------------------------
# AccessToken 클래스
class AccessToken :
    def __init__(self):
        self.starttime = datetime.now()
        self.APP_KEY = "App key"
        self.APP_SECRET = "App Secret key"
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
            host='localhost', user='user name', 
            password='password', port=3306, charset='utf8')

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
        self.api_key='api key'
    
    def GetApiKey(self):
        return self.api_key
