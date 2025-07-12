from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Category(BaseModel):
    id: str
    name: str
    url: str

class Article(BaseModel):
    id: str
    title: str
    sapo: str
    url: str
    image_url: str
    publication_time: str
    category: Category
    full_content: Optional[str] = None

class ArticleSummary(BaseModel):
    id: str
    title: str
    url: str

class Pagination(BaseModel):
    currentPage: int
    hasMore: bool

class CategoryInfo(BaseModel):
    id: str
    name: str

class TopStory(BaseModel):
    topStory: Article
    secondaryStories: List[Article]

class MostRead(BaseModel):
    title: str
    articles: List[ArticleSummary]

class ArticleStream(BaseModel):
    articles: List[Article]
    pagination: Pagination

class CategoryPageResponse(BaseModel):
    categoryInfo: CategoryInfo
    featuredContent: TopStory
    mostRead: MostRead
    articleStream: ArticleStream

class ArticlesResponse(BaseModel):
    articles: List[Article]
    pagination: Pagination

class ArticleDetailResponse(BaseModel):
    id: str
    title: str
    sapo: str
    url: str
    image_url: str
    publication_time: str
    category: Category
    full_content: str

class NavigationResponse(BaseModel):
    mainMenu: List[Category]
    extendedMenu: dict
    hotTopics: List[str]

class SearchResult(BaseModel):
    query: str
    type: str
    results: List[ArticleSummary]