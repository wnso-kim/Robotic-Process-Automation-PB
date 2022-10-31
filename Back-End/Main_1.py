import time
import schedule
from Base import DB
from Set_Price_Chart import PriceChart


# 시세 갱신 main 함수
if __name__ == '__main__':
    pc = PriceChart()         

    # 사용자가 선택한 종목 불러옴
    result = DB().GetKospiCode()

    # 월봉 시세 갱신
    # 스케쥴 : 4주마다 실행
    schedule.every(4).weeks.do(pc.SetMonthChart,result)  

    # 분봉 저장 함수
    pc.SetDayChart(result) 
    
    # 반복
    while True:
        schedule.run_pending()             # 스케쥴 실행
        time.sleep(0.001)                  # 오류 방지

        pc.SetPriceChart(result)           # 실시간 시세 갱신
        time.sleep(0.001)                  # 오류 방지
        
        
