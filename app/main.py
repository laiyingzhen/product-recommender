from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.modules.crawler.router import router as crawler_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# 1. 掛載靜態檔案 (CSS/JS)
#app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. 設定 HTML Template 引擎
templates = Jinja2Templates(directory="app/templates")

# 3. 註冊模組化的 Routers (未來新增模組就在這 include)
app.include_router(crawler_router)

# 4. 前端首頁路由
@app.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": settings.PROJECT_NAME})