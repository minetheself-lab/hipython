# routers/file_upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from transformers import pipeline

router = APIRouter(prefix="/analysis", tags=["감성분석"])

# 모델 로드 (서버 시작 시 1회만 실행)
classifier = pipeline(
    "text-classification",
    model="snunlp/KR-FinBert-SC"
)


@router.post("/sentiment")
async def upload_sentiment(file: UploadFile = File()):
    if file.content_type not in ["text/plain"]:
        raise HTTPException(
            status_code=400,
            detail="텍스트 파일(.txt)만 업로드 가능합니다"
        )
    contents = await file.read()
    text = contents.decode("utf-8")
    result = classifier(text)[0]
    return {
        "filename": file.filename,
        "text": text,
        "label": result["label"],
        "score": round(result["score"], 4)
    }
