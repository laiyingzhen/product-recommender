from pydantic import BaseModel
from typing import List, Optional

# 前端發送請求的格式
class SearchRequest(BaseModel):
    keyword: str          # 搜尋關鍵字，例如：除疤凝膠
    board: str = "BeautySalon" # 預設看板

# 單一產品統計結果
class ProductResult(BaseModel):
    product_name: str
    content_count: int
    comment_count: int
    total_count: int

# API 最終回傳格式
class SearchResponse(BaseModel):
    keyword: str
    csv_file_path: str
    results: List[ProductResult]