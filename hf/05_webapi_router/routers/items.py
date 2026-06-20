from fastapi import APIRouter

router=APIRouter(
  prefix="/items",
  tags=["종목", "ticker"]
)

# 임시 종목 데이터
ITEMS = [
    {"id": 1, "ticker": "005930", "name": "삼성전자"},
    {"id": 2, "ticker": "000660", "name": "SK하이닉스"},
    {"id": 3, "ticker": "035420", "name": "NAVER"},
]

@router.get('/')
def list_items():
    return ITEMS
  
@router.get("/{item_id}")
def get_item(item_id: int):
    for item in ITEMS:
        if item["id"] == item_id:
            return item
    return {"error": "존재하지 않는 종목입니다"}
  
  
