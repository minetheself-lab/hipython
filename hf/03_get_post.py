from fastapi import FastAPI

app = FastAPI()

# GET : 데이터 조회
@app.get("/hello")
def say_hello():
    return {"message": "안녕하세요"}


# POST : 데이터 전송
@app.post("/echo")
def echo(data: dict):
    return {"받은 데이터": data}

@app.get("/test1")
def root1():
  return {"name":"둘리"}

@app.get("/test2")
def root2():
  return ["둘리","또치","도우너"]

@app.get("/test3")
def root3():
  return "<h1>안녕?</h1>"

@app.get("/test4")
def root4():
  return 2000

#경로 매개 변수, 핸들러
@app.get("/items/{item_id}")
def read_item(item_id: int): 
  item_id=item_id*2
  print(f'{item_id}를 받았습니다')

  return {"ID": item_id}

#쿼리 매개변수 > ?뒤에 온다.
#엔드포인트 정의, 
#http://127.0.0.1:8000/items/3/discount?discount=true
@app.get("/items/{item_id}/discount")
def get_item(item_id: int, discount:bool):
  item_msg=f"{discount}할인여부"
  return item_msg

#http://127.0.0.1:8000/items/3/orders/2
@app.get("/items/{item_id}/orders/{order_id}")
def get_item_orders(item_id:int, order_id:int):
  print("get_item_orders")
  return {"item_id":item_id, "order_id":order_id}

#http://127.0.0.1:8000/stocks/005930/history?days=60&market=kospi
@app.get("/stocks/{ticker}/history")
def get_stock_history(
  ticker: str, days: int, market: str):
  print("get_stock_history > 종목 이력을 조회합니다.")
  return{"ticker":ticker, "days":days, "history":"구현예정입니다."}


from pydantic import BaseModel

class News(BaseModel):
  title: str
  content: str
  views: int=0
  

# POST : 데이터 전송 추가
@app.post("/news")
def anal_news(data: News):
  print(f"{data.views}회 조회되었습니다.")
  return {"news":data.views}


class News(BaseModel):
  ticker: str
  days: int
  market: str


#http://127.0.0.1:8000/stocks/005930/history?days=60&market=kospi
@app.post("/stocks")
def post_stocks(data: News):
  return{"stocks":data}



