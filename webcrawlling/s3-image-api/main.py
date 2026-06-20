from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from s3_client import s3, BUCKET_NAME
from database import ImageHistory, get_db, init_db
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/images/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(ImageHistory)
        .filter(ImageHistory.user_id == user_id)
        .order_by(ImageHistory.uploaded_at.desc())
        .all()
    )
    return {
        "user_id": user_id,
        "count": len(records),
        "history": [
            {
                "id": r.id,
                "filename": r.filename,
                "url": r.url,
                "size": r.size,
                "uploaded_at": str(r.uploaded_at),
            }
            for r in records
        ],
    }

@app.post("/images")
async def upload_image(
    user_id: str = Query(default="guest", description="사용자 ID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    key = f"{uuid.uuid4()}.{ext}"
    try:
        s3.upload_fileobj(
            file.file,
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    region = os.getenv("AWS_REGION")
    url = f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{key}"
    record = ImageHistory(
        user_id=user_id,
        filename=key,
        url=url,
        size=file.size,
    )
    db.add(record)
    db.commit()
    return {"filename": key, "url": url, "user_id": user_id}

@app.get("/images")
def list_images():
    ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
    region = os.getenv("AWS_REGION")
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    objects = response.get("Contents", [])
    images = [
        {
            "filename": obj["Key"],
            "url": f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{obj['Key']}",
            "size": obj["Size"],
            "last_modified": str(obj["LastModified"]),
        }
        for obj in objects
        if obj["Key"].rsplit(".", 1)[-1].lower() in ALLOWED_EXT
    ]
    return {"count": len(images), "images": images}

@app.delete("/images/{filename}")
def delete_image(filename: str):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"{filename} 삭제 완료"}