from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.figure import Figure
from Base import DB, PATH, Pandas
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from win10toast import ToastNotifier
from Widget import WidgetClass
from datetime import datetime, timedelta


#--------------------------------------------------------------------------
# Main UI Path 지정
form = PATH.resource_path('Main.ui')
Main_form = uic.loadUiType(form)[0]
    
#--------------------------------------------------------------------------
# Main Window ui
class WindowClass(QMainWindow, Main_form):
    def __init__(self):                                            
        super( ).__init__( )
        self.setupUi(self)
        self.setWindowTitle("업무자동화 프로그램")
        self.Pd = Pandas()

        self.make_widget()
        # PlusButton 클릭 이벤트 연결
        self.PlusButton.clicked.connect(self.btn_click_plus)
        self.RefreshButton.clicked.connect(self.make_widget)
        self.ExcelButton.clicked.connect(self.btn_click_excel)

        # QTimer timeout 이벤트 연결
        self.timer = QTimer(self)
        self.timer.start(10000) #10sec 마다 반복
        self.timer.timeout.connect(self.check_price)
        

#--------------------------------------------------------------------------
# 위젯 생성 함수
    def make_widget(self):
        # 사용자가 선택한 종목을 기반으로 widget 생성
        self.Pd = Pandas()
        list = self.Pd.list_return()

        # Main 스크롤에 widget 추가
        # SALayout 변수 생성 -> Main의 scrolAreaLayout 지정
        SALayout = self.scrollAreaLayout

        for i in reversed(range(SALayout.count())): 
            SALayout.itemAt(i).widget().setParent(None)

        for text in list:
            wid = WidgetClass(text)
            SALayout.addWidget(wid)

#--------------------------------------------------------------------------
# 목표시세 도달 확인 함수
    def check_price(self):
        db = DB()
        cursor = db.GetCursor()
        cursor.execute('use kis_api')

        price_list = []
        SALayout = self.scrollAreaLayout
        for i in range(SALayout.count()): 
            price_ = SALayout.itemAt(i).widget().target_price_
            name_ = SALayout.itemAt(i).widget().stock_name
            price_list.append({name_:price_})

            select = f'SELECT datetime,{name_} FROM kis_api.price order by datetime desc;'
            cursor.execute(select)
            data = cursor.fetchone()
            if price_<=data[name_]:
                self.toast(name_)
   
#--------------------------------------------------------------------------  
# 기타 함수

    # 윈도우 알림 함수
    def toast(self, stock_name):
        toaster = ToastNotifier()
        toaster.show_toast(f'{stock_name} 목표 시세 도달', icon_path=None,duration=5,threaded=True)

    # plus 버튼 클릭 이벤트 함수
    def btn_click_plus(self):
        # 사용자가 입력한 text를 읽어옴
        text = self.SerchLine.text()
        self.Pd.append(text)
        self.make_widget()

    # 엑셀 변환 버튼 클릭 이벤트 함수
    def btn_click_excel(self):
        # DB연결
        db = DB()
        cursor = db.GetCursor()
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 선택한 종목 Excel로 변환
        stock_name_list = self.Pd.list_return()
        for name in stock_name_list:
            # 오늘 시세
            if datetime.now().strftime('%H%M%S')<'090000':
                time_s = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d 09:00:00')
                time_e = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d 15:30:00')
            else:
                time_s = datetime.now().strftime('%Y-%m-%d 09:00:00')
                time_e = datetime.now().strftime('%Y-%m-%d 15:30:00')
            select = f'SELECT datetime,{name} FROM kis_api.price where datetime between "{time_s}" AND "{time_e}" order by datetime desc;'
            cursor.execute(select)
            price = cursor.fetchall()
            price = pd.DataFrame(price)

            # 월봉
            select = f'SELECT date,{name} FROM kis_api.price_month order by date;'
            cursor.execute(select)
            price_m = cursor.fetchall()
            price_m = pd.DataFrame(price_m)

            # 뉴스
            time_s = (datetime.now() - timedelta(days=7))
            time_s = time_s.strftime('%Y-%m-%d %H:%M:%S')
            time_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            select = f'SELECT * FROM news_research.news where datetime between "{time_s}" AND "{time_e}" AND name="{name}" order by datetime desc;'
            cursor.execute(select)
            news = cursor.fetchall()
            news = pd.DataFrame(news)

            # 리서치
            select = f'SELECT * FROM news_research.research where (datetime between "{time_s}" AND "{time_e}") AND (name="{name}" OR ISNULL(name)) order by datetime desc;'
            cursor.execute(select)
            research = cursor.fetchall()
            research = pd.DataFrame(research)

            # 공시
            time_s = (datetime.now() - timedelta(days=50))
            time_s = time_s.strftime('%Y-%m-%d %H:%M:%S')
            time_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            select = f'SELECT * FROM dart_api.public_notice where datetime between "{time_s}" AND "{time_e}" AND name="{name}" order by datetime desc;'
            cursor.execute(select)
            pnotice = cursor.fetchall()
            pnotice = pd.DataFrame(pnotice)

            # 파일 이름 지정
            file_name = f'{name}_{date}.xlsx'
            # Excel 변환
            with pd.ExcelWriter(file_name) as writer:
                price.to_excel(writer, sheet_name = '시세')
                price_m.to_excel(writer, sheet_name = '월봉')
                news.to_excel(writer, sheet_name = '기사')
                research.to_excel(writer, sheet_name = '리서치')
                pnotice.to_excel(writer, sheet_name = '공시')
