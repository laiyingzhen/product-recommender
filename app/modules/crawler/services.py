import os
import json
import urllib.parse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Tuple
from google import genai
from google.genai import types

from app.config import settings
from app.modules.crawler.schemas import ProductResult


class PttService:
    # 1. PTT 爬蟲相關設定
    PTT_DOMAIN = "https://www.ptt.cc"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "over18=1",  # 自動通過 PTT 年齡認證
    }

    @classmethod
    def fetch_ptt_article_urls(cls, keyword: str, board: str, max_articles: int = 5) -> List[str]:
        """向 PTT 板塊發送搜尋請求，取得前 N 篇相關文章的網址"""
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{cls.PTT_DOMAIN}/bbs/{board}/search?q={encoded_keyword}"

        response = requests.get(search_url, headers=cls.HEADERS, timeout=10)
        if response.status_code != 200:
            raise Exception(f"無法存取 PTT 搜尋頁面 (Status: {response.status_code})")

        soup = BeautifulSoup(response.text, "html.parser")
        article_urls = []

        for title_div in soup.find_all("div", class_="title"):
            a_tag = title_div.find("a")
            if a_tag and a_tag.get("href"):
                full_url = cls.PTT_DOMAIN + a_tag["href"]
                article_urls.append(full_url)
                if len(article_urls) >= max_articles:
                    break

        return article_urls

    @classmethod
    def extract_article_content(cls, article_url: str) -> str:
        """解析單一 PTT 文章網頁，取出標題、內文與推文文字"""
        try:
            response = requests.get(article_url, headers=cls.HEADERS, timeout=10)
            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.text, "html.parser")
            main_content = soup.find("div", id="main-content")

            if not main_content:
                return ""

            # 抓取推文
            push_texts = []
            for push in main_content.find_all("div", class_="push"):
                push_content = push.find("span", class_="push-content")
                if push_content:
                    push_texts.append(push_content.text.strip(": "))
                push.extract()

            # 清理元資料
            for meta in main_content.find_all("div", class_=lambda c: c and "article-metaline" in c):
                meta.extract()

            content_text = main_content.text.strip()
            return f"【文章內容】:\n{content_text}\n\n【推文/回文列表】:\n" + "\n".join(push_texts)

        except Exception as e:
            print(f"抓取單篇文章失敗 ({article_url}): {e}")
            return ""

    @classmethod
    def parse_products_with_gemini(cls, combined_text: str) -> List[dict]:
        """呼叫 Gemini 1.5 Flash 解析文本中的商品名稱與出現次數"""
        # 初始化最新的 Google GenAI Client
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("未設定 GEMINI_API_KEY，請檢查 .env 檔案")

        client = genai.Client(api_key=api_key)

        prompt = f"""
你是一個精準的文字分析專家。請閱讀以下來自 PTT 看板的文章與推文，幫我找出所有被提及的「保養品/藥膏/產品名稱」。

分析規則：
1. 請包含產品全名、品牌名稱或常見俗稱（例如：玻麗舒、倍舒痕、海洋拉娜、小棕瓶）。
2. 請精準統計該產品在「文章內文」與「推文」中出現的次數。
3. 排除一般性詞彙（例如：醫生、皮膚科、效果、藥局、診所）。
4. 請以 JSON 陣列格式輸出。

PTT 內容：
{combined_text}
"""

        # 設定以強制 JSON 格式輸出 (Structured Output)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return []

    @classmethod
    async def process_search(cls, keyword: str, board: str = "BeautySalon") -> Tuple[List[ProductResult], str]:
        """整合流程：爬蟲 -> AI 解析 -> 資料加總 -> 儲存 CSV"""
        # 1. 抓取文章 URL (預設抓最新 5 篇做分析)
        urls = cls.fetch_ptt_article_urls(keyword, board, max_articles=5)

        if not urls:
            raise Exception(f"在 PTT {board} 板找不到與 '{keyword}' 相關的文章")

        # 2. 爬取並合併多篇文章內容
        all_text_blocks = []
        for url in urls:
            text = cls.extract_article_content(url)
            if text:
                all_text_blocks.append(text)

        full_corpus = "\n\n=====================\n\n".join(all_text_blocks)

        # 3. 送交 Gemini AI 解析
        ai_raw_results = cls.parse_products_with_gemini(full_corpus)

        # 4. 使用 Pandas 進行多筆產品數據加總整理
        if not ai_raw_results:
            return [], ""

        df = pd.DataFrame(ai_raw_results)

        # 容錯處理欄位名稱
        if "content_count" not in df.columns:
            df["content_count"] = 0
        if "comment_count" not in df.columns:
            df["comment_count"] = 0

        # 將相同產品名稱的次數歸併相加
        df_grouped = df.groupby("product_name", as_index=False).agg({
            "content_count": "sum",
            "comment_count": "sum"
        })

        df_grouped["total_count"] = df_grouped["content_count"] + df_grouped["comment_count"]
        df_grouped = df_grouped.sort_values(by="total_count", ascending=False)

        # 5. 轉為 Pydantic Response 格式
        final_results = [
            ProductResult(
                product_name=row["product_name"],
                content_count=int(row["content_count"]),
                comment_count=int(row["comment_count"]),
                total_count=int(row["total_count"])
            )
            for _, row in df_grouped.iterrows()
        ]

        # 6. 存成 CSV 檔
        os.makedirs("data", exist_ok=True)
        csv_path = f"data/{keyword}_result.csv"
        df_grouped.to_csv(csv_path, index=False, encoding="utf-8-sig")

        return final_results, csv_path