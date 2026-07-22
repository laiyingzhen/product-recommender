from fastapi import APIRouter, HTTPException
from app.modules.crawler.schemas import SearchRequest, SearchResponse
from app.modules.crawler.services import PttService

router = APIRouter(
    prefix="/api/v1/crawler",
    tags=["PTT 爬蟲與推薦 API"]
)

@router.post("/search", response_model=SearchResponse)
async def search_products(payload: SearchRequest):
    try:
        results, csv_path = await PttService.process_search(
            keyword=payload.keyword, 
            board=payload.board
        )
        return SearchResponse(
            keyword=payload.keyword,
            csv_file_path=csv_path,
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))