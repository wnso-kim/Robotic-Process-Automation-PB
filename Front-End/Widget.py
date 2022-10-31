import matplotlib.pyplot as plt
from matplotlib.dates import num2date
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.figure import Figure
from Base import DB, PATH
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5 import uic
from datetime import datetime, timedelta

#--------------------------------------------------------------------------  
# Widget ui
form = PATH.resource_path('Set_Widget.ui')
Set_form = uic.loadUiType(form)[0]
# News Research PublicNotice ui
form = PATH.resource_path('News_Research_PublicNotice.ui')
NSP_form = uic.loadUiType(form)[0]

#--------------------------------------------------------------------------  
# News Research PublicNotice Widget Class
class NSPWidgetClass(QWidget, NSP_form):
    def __init__(self):                                           
        super( ).__init__( )
        self.setupUi(self)

#--------------------------------------------------------------------------          
# Widget Set Class
class WidgetClass(QWidget, Set_form):
    def __init__(self, stock_name):                                           
        super( ).__init__( )
        self.setupUi(self)
        self.stock_name = stock_name
        self.target_price_ = None
        self.togglebutton.toggled.connect(self.slot_toggle)
        self.setButton.clicked.connect(self.slot_btn)
        self.SetPrice()
        self.SetMonth()
        self.SetNews()
        self.SetResearch()
        self.SetPublicNotice()

#-------------------------------------------------------------------------- 
# 이벤트 함수
    def slot_toggle(self,state):
        self.togglebutton.setText({True:'월봉 차트 변환',False: "일봉 차트 변환"}[state])
        self.Chart.setCurrentWidget({True:self.ChartPage1,False: self.ChartPage2}[state])

    def slot_btn(self):
        text = self.target_price_text.text()
        self.target_price_ = int(text)

    def on_press_day(self, event):
        x = num2date(event.xdata).strftime('%m월%d일 %H:%M:%S')
        self.coordinateLabel.setText(x)

        y = f'{int(event.ydata)} 원'
        self.priceLabel.setText(y)

    def on_press_month(self, event):
        x = num2date(event.xdata).strftime('%Y년%m월%d일')
        self.coordinateLabel.setText(x)

        y = f'{int(event.ydata)} 원'
        self.priceLabel.setText(y)

#--------------------------------------------------------------------------   
# 시세 차트 출력 함수       
    def SetPrice(self):
        self.Chart.setCurrentWidget(self.ChartPage1)
        canvas = FigureCanvas(Figure())
        layout = self.ChartPage1Layout
        layout.addWidget(canvas)
        
        
        plt.rc('font', family='Malgun Gothic')
        plt.rc('axes', unicode_minus=False)

        splot = canvas.figure.subplots()
       
        data = self.GetPrice()
        df = pd.DataFrame(data)
        df.plot(kind='line',x='datetime',y=self.stock_name, ax=splot, legend=None, x_compat=True)
        splot.set_title(self.stock_name, fontsize=10)
        
        # 목표가 지정
        self.target_price_ = int(data[0][self.stock_name] * 1.3)
        self.target_price_text.setText(str(self.target_price_))
        
        # chart x축 조정
        datestr = data[0]['datetime'].strftime('%Y-%m-%d')
        splot.set_xlim((f'{datestr} 09:00:00',f'{datestr} 15:30:00'))
        splot.set_xticks([f'{datestr} 09:00:00',f'{datestr} 11:00:00',f'{datestr} 13:00:00',f'{datestr} 15:30:00']) 
        splot.set_xticklabels(['9:00','11:00','13:00','15:30'], fontsize=8, rotation=0, ha='center')
        splot.axes.yaxis.set_visible(False)

        # 현재 시세 설정 및 마우스 이벤트 연동
        self.coordinateLabel.setText(data[0]['datetime'].strftime('%m월%d일 %H:%M:%S'))
        self.priceLabel.setText(str(data[0][self.stock_name]))
        canvas.mpl_connect("button_press_event", self.on_press_day)

#--------------------------------------------------------------------------  
# 현재 시세 DB에서 얻어오는 함수
    def GetPrice(self):
        db = DB()
        cursor = db.GetCursor()
        cursor.execute('use kis_api')

        day = 0
        data = None
        while True:
            time_s = (datetime.now() - timedelta(days = day)).strftime('%Y-%m-%d 09:00:00')
            time_e = (datetime.now() - timedelta(days = day)).strftime('%Y-%m-%d 15:30:00') 

            select = f'SELECT datetime,{self.stock_name} FROM kis_api.price where datetime between "{time_s}" AND "{time_e}" AND minute(datetime)%10=0 order by datetime desc;'
            cursor.execute(select)
            data = cursor.fetchall()

            if not data:
                day = day + 1
                continue
                        
            break
        

        return data

#--------------------------------------------------------------------------  
# 월봉 차트 출력 함수
    def SetMonth(self):
        canvas = FigureCanvas(Figure())
        layout = self.ChartPage2Layout
        layout.addWidget(canvas)
        
        plt.rc('font', family='Malgun Gothic')
        plt.rc('axes', unicode_minus=False)

        splot = canvas.figure.subplots()
       
        data = self.GetMonth()
        df = pd.DataFrame(data)
        df.plot(kind='line',x='date',y=self.stock_name, ax=splot, legend=None)
        splot.set_title(self.stock_name, fontsize=10)
        
        splot.axes.yaxis.set_visible(False)
        # 마우스 이벤트 연동
        canvas.mpl_connect("button_press_event", self.on_press_month)

#--------------------------------------------------------------------------  
# 월봉 차트 DB에서 얻어오는 함수
    def GetMonth(self):
        db = DB()
        cursor = db.GetCursor()
        cursor.execute('use kis_api')
        select = f'SELECT date,{self.stock_name} FROM kis_api.price_month order by date;'
        cursor.execute(select)
        data = cursor.fetchall()

        return data

#--------------------------------------------------------------------------  
# 뉴스 탭에 출력하는 함수
    def SetNews(self):
        # News 스크롤에 위젯 추가
        SALayout = self.NewsScrollLayout

        df = self.GetNews()
        for row in df:
            news = NSPWidgetClass()
            url_ = row['url']
            title_ = row['title']
            press_ = row['press']
            date_ = row['datetime'].strftime('%Y-%m-%d')
            news.Title.setText(f'<a href="{url_}">{title_}</a>')
            news.Press.setText(press_)
            news.Date.setText(date_)
            # 하이퍼링크 추가
            news.Title.setOpenExternalLinks(True)
            SALayout.addWidget(news)

#--------------------------------------------------------------------------  
# 뉴스 DB에서 얻어오는 함수   
    def GetNews(self):
        time_s = (datetime.now() - timedelta(days=7))
        time_s = time_s.strftime('%Y-%m-%d %H:%M:%S')
        time_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db = DB()
        cursor = db.GetCursor()

        select = f'SELECT * FROM news_research.news where datetime between "{time_s}" AND "{time_e}" AND name="{self.stock_name}" order by datetime desc;'
        cursor.execute(select)

        data = cursor.fetchall()
        return data

#--------------------------------------------------------------------------  
# 리서치 탭에 출력하는 함수
    def SetResearch(self):
        # Research 스크롤에 위젯 추가
        SALayout = self.ResearchScrollLayout

        data = self.GetResearch()
        for row in data:
            research = NSPWidgetClass()
            url_ = row['pdf_url']
            title_ = row['title']
            company_ = row['company']
            date_ = row['datetime'].strftime('%Y-%m-%d')
            research.Title.setText(f'<a href="{url_}">{title_}</a>')
            research.Press.setText(company_)
            research.Date.setText(date_)
            # 하이퍼링크 추가
            research.Title.setOpenExternalLinks(True)
            SALayout.addWidget(research)

#--------------------------------------------------------------------------  
# 리처시 DB에서 얻어오는 함수     
    def GetResearch(self):
        time_s = (datetime.now() - timedelta(days=7))
        time_s = time_s.strftime('%Y-%m-%d %H:%M:%S')
        time_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db = DB()
        cursor = db.GetCursor()

        select = f'SELECT * FROM news_research.research where (datetime between "{time_s}" AND "{time_e}") AND (name="{self.stock_name}" OR ISNULL(name)) order by datetime desc;'
        cursor.execute(select)

        data = cursor.fetchall()
        return data

#--------------------------------------------------------------------------  
# 공시 탭에 출력하는 함수
    def SetPublicNotice(self):
        # PublicNotice 스크롤에 위젯 추가
        SALayout = self.PublicNoticeScrollLayout

        df = self.GetPublicNotice()
        for row in df:
            Pnotice = NSPWidgetClass()
            url_ = row['pdf_url']
            title_ = row['title']
            name_ = row['name']
            date_ = row['datetime'].strftime('%Y-%m-%d')
            Pnotice.Title.setText(f'<a href="{url_}">{title_}</a>')
            Pnotice.Press.setText(name_)
            Pnotice.Date.setText(date_)
            # 하이퍼링크 추가
            Pnotice.Title.setOpenExternalLinks(True)
            SALayout.addWidget(Pnotice)

#--------------------------------------------------------------------------  
# 공시 DB에서 얻어오는 함수    
    def GetPublicNotice(self):
        time_s = (datetime.now() - timedelta(days=50))
        time_s = time_s.strftime('%Y-%m-%d %H:%M:%S')
        time_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db = DB()
        cursor = db.GetCursor()

        select = f'SELECT * FROM dart_api.public_notice where datetime between "{time_s}" AND "{time_e}" AND name="{self.stock_name}" order by datetime desc;'
        cursor.execute(select)

        data = cursor.fetchall()
        return data