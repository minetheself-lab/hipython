from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title='금융뉴스 감성분석서비스')



# 모델 로드 (서버 시작 시 1회만 실행)
classifier = pipeline(
    "text-classification",
    model="snunlp/KR-FinBert-SC"
)

class TextRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float

@app.post("/sentiment",response_model=SentimentResponse )
def analyze_sentiment(request:TextRequest):
  #분류모델 호출
  result=classifier(request.text)[0]
  return SentimentResponse(
    text=request.text,
    label=result["label"],
    score=round(result["score"], 4)
    )

from fastapi.middleware.cors import CORSMiddleware
# CORS 설정: 모든 출처, 모든 메소드, 모든 헤더를 허용합니다.
# 실제 서비스에서는 보안을 위해 출처를 명시하는 것이 좋습니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/items/{item_id}")
def read_item(item_id: int):
    print(f'hello {item_id}')
    return {"item_id": item_id, "name": "슈퍼컴퓨터"}
