import time
from Base import DB
from Set_Public_Notice import Dart
from Set_News_Research import Crawler

# 공시 | 리서치 | 기사 갱신 main 함수
if __name__ == '__main__':
    dart = Dart()
    cw = Crawler()

    # 사용자가 선택한 종목 불러옴
    result = DB().GetKospiCode()

    # 50일 간의 공시 정보 저장 함수
    dart.SetPublicNotice(result, 50)
    # 1일간의 기사 갱신
    cw.News(result, 4) 
                     
    #반복
    while True:
        dart.SetPublicNotice(result, 1)     # 실시간 공시 갱신
        
        time.sleep(0.001)                  # 오류 방지
        
        cw.Research_1()                     # 실시간 리서치 갱신
        cw.Research_2()                     #   ``
        cw.Research_3()                     #   ``
        cw.News(result, 7)                  # 실시간 기사 갱신(1시간)

        time.sleep(0.001)                  # 오류 방지