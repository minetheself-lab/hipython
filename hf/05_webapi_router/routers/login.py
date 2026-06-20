# routers/login.py

from fastapi import APIRouter, Form, HTTPException

router = APIRouter(prefix="/auth", tags=["인증"])

# 임시 사용자 데이터 (실제 서비스는 DB 사용)
USERS = {
    "admin": "1234",
    "student": "abcd"
}


@router.post("/login")
def login(username: str = Form(), password: str = Form()):
    if username not in USERS:
        raise HTTPException(status_code=401, detail="존재하지 않는 사용자입니다")
    if USERS[username] != password:
        raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다")
    return {"message": f"{username}님 로그인 성공"}
