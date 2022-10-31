from symbol import except_clause
import pymysql
import pandas as pd
import os
import sys

#--------------------------------------------------------------------------
# DB 클래스
class DB :
    def __init__(self):
        self.db = pymysql.connect(
            host='3.39.234.81', user='wc', 
            password='root', port=3306, charset='utf8')

    # 커서 반환 함수
    def GetCursor(self):
        # DB cursor 반환
        return self.db.cursor(pymysql.cursors.DictCursor)   

    # 종목 이름, 코드 받아오는 함수
    def GetKospiCode(self):
        cursor = self.GetCursor()
        cursor.execute('select * from kospi_code.code')
        result = cursor.fetchall()
        return result

    # mysql commit 함수
    def Commit(self):
        self.db.commit()


#--------------------------------------------------------------------------
# PATH 클래스
class PATH:
    def resource_path(relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    
        return os.path.join(base_path, relative_path)


#--------------------------------------------------------------------------
# Pandas_ 클래스
class Pandas:
    def __init__(self):
        try:
            self.df = pd.read_csv(PATH.resource_path('User_Select.csv'))
        except:
            self.make_csv()
            self.df = pd.read_csv(PATH.resource_path('User_Select.csv'))


    # csv 파일이 없는경우 만드는 함수
    def make_csv(self):
        list = [{'종목':'한국금융지주'}]
        df = pd.DataFrame(list)
        df.to_csv('User_Select.csv')
    
    # csv 파일을 읽어 종목 리스트 반환 함수
    def list_return(self):
        self.df = pd.read_csv(PATH.resource_path('User_Select.csv'))
        list = []

        for idx in self.df.index:
            val = self.df.iloc[idx, 1]
            list.append(val)

        return list
    
    # csv파일에 종목 추가하는 함수
    def append(self, stock_name):
        new_row = pd.DataFrame([{'종목':stock_name}])
        self.df = pd.concat([self.df.iloc[:0], new_row, self.df.iloc[0:]], ignore_index=True)

        self.df.to_csv(PATH.resource_path('User_Select.csv'), index=False)
        
