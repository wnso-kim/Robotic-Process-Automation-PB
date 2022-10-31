import pandas as pd
from Base import DB

# pandas로 excel 파일 읽어오기
filename = 'kospi_code.xlsx'
# ['단축코드', '한글명', '그룹코드']
df = pd.read_excel(filename, usecols=[0,2,3] ,engine='openpyxl')


# 딕셔너리에 {'한글명' : '단축코드'} 넣기
kospi_dict = {}
for row in df.itertuples() :
    # 선물(EN, EF), 부동산(BC), 신주인수권증권(SW) 제외
    if row[3]=='EN' or row[3]=='EF' or row[3]=='BC' or row[3]=='SW': continue
    # 딕셔너리 추가
    kospi_dict[row[2]] = row[1]  

# DB connect
db = DB()
cursor = db.GetCursor()

# DB 삽입
dlist = []
for key,value in kospi_dict.items():
    dlist.append({'name':key, 'stock_code':value})

# insert
cursor.execute('USE kospi_code')
insert = f"insert into `code` (name,stock_code) values (%(name)s, %(stock_code)s) as new on duplicate key update stock_code = new.stock_code;"
cursor.executemany(insert, dlist)
# 커밋
db.Commit()

# DB 종료
db.Close()