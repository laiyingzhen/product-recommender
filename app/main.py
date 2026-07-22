import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.modules.crawler.router import router as crawler_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# 自動建立 static 資料夾（防範目錄不存在的報錯）
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 設定 HTML Template 引擎
templates = Jinja2Templates(directory="app/templates")

# 註冊 API 路由
app.include_router(crawler_router)

# 1. 系統首頁路由
@app.get("/")
async def home_page(request: Request):
    # 新版語法：第一個參數傳入 request，第二個參數 context 傳入其他變數 (若無可傳空字典 {})
    return templates.TemplateResponse(request, "index.html", context={})