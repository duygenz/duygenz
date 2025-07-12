from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from .scraper import scrape_articles

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="CafeF News API",
    description="API không chính thức để lấy các bài báo từ mục Thị trường chứng khoán của CafeF.",
    version="1.0.0"
)

# Pydantic model để định nghĩa cấu trúc dữ liệu trả về
class Article(BaseModel):
    title: str
    link: str
    image_url: str
    published_date: str

@app.get("/api/v1/articles", 
         response_model=List[Article],
         summary="Lấy danh sách bài viết mới nhất",
         tags=["Articles"])
async def get_articles():
    """
    Endpoint này thực hiện cào dữ liệu từ trang CafeF và trả về danh sách
    các bài viết mới nhất trong mục Thị trường chứng khoán.
    """
    articles_data = scrape_articles()
    return articles_data

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Chào mừng đến với CafeF News API. Truy cập /docs để xem tài liệu."}
