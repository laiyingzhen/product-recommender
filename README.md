# 批踢踢實業坊產品推薦系統
## 使用技術：
### Python 3.12.0 + Fast API
+ 使用技術
  - Python 3.12.0 + Fast API

## 伺服器啟動指令：
### uvicorn app.main:app --reload
## 啟動方式：
### 開啟瀏覽器訪問：http://127.0.0.1:8000/docs
### 點開 POST /api/v1/crawler/search 點擊 Try it out，輸入

``` js
{
  "keyword": "除疤凝膠",
  "board": "BeautySalon"
}
```
### 點擊 Execute 執行，系統就會自動爬取最新的 PTT 美妝板文章、透過 Gemini 1.5 Flash 提取產品統計，並將結果輸出為 JSON 以及儲存到 data/除疤凝膠_result.csv

