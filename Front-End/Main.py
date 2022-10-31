from Main_Widget import  WindowClass
from PyQt5.QtWidgets import *
import sys


#--------------------------------------------------------------------------
# main 함수
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = WindowClass( )   # Main Window 생성
    myWindow.show()             # Main Window 실행
    app.exec_()             