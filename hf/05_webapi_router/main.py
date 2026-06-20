from fastapi import FastAPI
from routers.items import router as items_router
from routers.login import router as login_router
from routers.file_upload import router as file_upload_router

app=FastAPI()
app.include_router(items_router)
app.include_router(login_router)
app.include_router(file_upload_router)

# 아나콘다 프롬프트에서 실행
# - cmd 화면에서 해당 경로로 이동: cd C:\Users\Admin\hipython\hf
# - conda activate hf-nlp
#uvicorn main:app --reload
#get/items/
#get/items/item/1
#get/items/item/2
#post/auth/login
#formed data로 입력
