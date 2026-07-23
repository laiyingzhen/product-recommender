from fastapi import APIRouter, HTTPException
from app.modules.crawler.schemas import SearchRequest, SearchResponse
from app.modules.crawler.services import PttService
import time

router = APIRouter(
    prefix="/api/v1/crawler",
    tags=["PTT 爬蟲與推薦 API"]
)

@router.post("/search", response_model=SearchResponse)
async def search_products(payload: SearchRequest):
    # ⏱️ 記錄整支 API 開始時間
    total_start = time.perf_counter()    
    try:
        results, csv_path = await PttService.process_search(
            keyword=payload.keyword, 
            board=payload.board
        )
        total_duration = time.perf_counter() - total_start
        print(f"🚀 [Log] ===== 查詢任務總耗時: {total_duration:.2f} 秒 =====\n")        
        return SearchResponse(
            keyword=payload.keyword,
            csv_file_path=csv_path,
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))