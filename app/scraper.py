import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
import time

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://m.cafef.vn"
TARGET_URL = f"{BASE_URL}/thi-truong-chung-khoan.chn"

def get_headers():
    """Trả về headers cho requests"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

def extract_article_id(url: str) -> str:
    """Trích xuất ID bài viết từ URL"""
    if not url:
        return str(int(time.time()))
    
    # Tìm pattern ID trong URL
    match = re.search(r'/(\d+)\.chn', url)
    if match:
        return match.group(1)
    
    # Fallback: tạo ID từ timestamp
    return str(int(time.time()))

def parse_date(date_str: str) -> str:
    """Chuyển đổi chuỗi ngày thành format ISO"""
    try:
        # Xử lý các format ngày khác nhau
        if 'hôm nay' in date_str.lower():
            return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        elif 'hôm qua' in date_str.lower():
            yesterday = datetime.now().replace(day=datetime.now().day - 1)
            return yesterday.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            # Giả sử format: "12/07/2025 12:40"
            date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            return date_obj.strftime("%Y-%m-%dT%H:%M:%S")
    except:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def scrape_articles(category_id: str = "thi-truong-chung-khoan", page: int = 1) -> List[Dict]:
    """Cào dữ liệu các bài báo từ trang chuyên mục"""
    try:
        url = f"{BASE_URL}/{category_id}.chn"
        if page > 1:
            url += f"?page={page}"
            
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Tìm container chứa danh sách bài viết
        list_container = soup.find('div', class_='lst')
        if not list_container:
            logger.warning("Không tìm thấy container chứa danh sách bài viết")
            return []

        # Tìm tất cả các item bài viết
        article_items = list_container.find_all('div', class_='box-category-item')

        for item in article_items:
            title_tag = item.find('a', class_='item-title')
            img_tag = item.find('img')
            date_tag = item.find('div', class_='time')
            sapo_tag = item.find('div', class_='item-desc')

            if not title_tag:
                continue

            title = title_tag.text.strip()
            link_relative = title_tag.get('href', '')
            link = f"{BASE_URL}{link_relative}" if link_relative and not link_relative.startswith('http') else link_relative
            image_url = img_tag.get('src', '') if img_tag else ""
            published_date = parse_date(date_tag.text.strip()) if date_tag else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            sapo = sapo_tag.text.strip() if sapo_tag else ""

            article_id = extract_article_id(link_relative)
            
            articles.append({
                "id": article_id,
                "title": title,
                "sapo": sapo,
                "url": link_relative,
                "image_url": image_url,
                "publication_time": published_date,
                "category": {
                    "id": category_id,
                    "name": "Thị trường chứng khoán",
                    "url": f"/{category_id}.chn"
                }
            })

        return articles

    except Exception as e:
        logger.error(f"Lỗi khi cào dữ liệu: {e}")
        return []

def scrape_article_detail(article_id: str) -> Optional[Dict]:
    """Cào chi tiết một bài viết cụ thể"""
    try:
        # Tìm URL bài viết từ ID
        url = f"{BASE_URL}/tin-tuc/{article_id}.chn"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trích xuất thông tin chi tiết
        title_tag = soup.find('h1', class_='title')
        sapo_tag = soup.find('div', class_='sapo')
        content_tag = soup.find('div', class_='content')
        date_tag = soup.find('div', class_='time')
        img_tag = soup.find('img', class_='main-img')

        title = title_tag.text.strip() if title_tag else ""
        sapo = sapo_tag.text.strip() if sapo_tag else ""
        full_content = str(content_tag) if content_tag else ""
        published_date = parse_date(date_tag.text.strip()) if date_tag else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        image_url = img_tag.get('src', '') if img_tag else ""

        return {
            "id": article_id,
            "title": title,
            "sapo": sapo,
            "url": f"/tin-tuc/{article_id}.chn",
            "image_url": image_url,
            "publication_time": published_date,
            "category": {
                "id": "thi-truong-chung-khoan",
                "name": "Thị trường chứng khoán",
                "url": "/thi-truong-chung-khoan.chn"
            },
            "full_content": full_content
        }

    except Exception as e:
        logger.error(f"Lỗi khi cào chi tiết bài viết {article_id}: {e}")
        return None

def scrape_category_page(category_id: str = "thi-truong-chung-khoan") -> Dict:
    """Cào dữ liệu trang chuyên mục hoàn chỉnh"""
    try:
        url = f"{BASE_URL}/{category_id}.chn"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Lấy tin nổi bật
        featured_articles = scrape_articles(category_id, 1)[:3]
        
        # Lấy tin đọc nhiều (giả lập)
        most_read_articles = scrape_articles(category_id, 1)[:5]
        
        # Lấy danh sách tin chính
        main_articles = scrape_articles(category_id, 1)[3:10]

        return {
            "categoryInfo": {
                "id": category_id,
                "name": "Thị trường chứng khoán"
            },
            "featuredContent": {
                "topStory": featured_articles[0] if featured_articles else {},
                "secondaryStories": featured_articles[1:3] if len(featured_articles) > 1 else []
            },
            "mostRead": {
                "title": "Đọc nhiều",
                "articles": [{"id": a["id"], "title": a["title"], "url": a["url"]} for a in most_read_articles]
            },
            "articleStream": {
                "articles": main_articles,
                "pagination": {
                    "currentPage": 1,
                    "hasMore": True
                }
            }
        }

    except Exception as e:
        logger.error(f"Lỗi khi cào trang chuyên mục: {e}")
        return {}

def scrape_navigation() -> Dict:
    """Cào dữ liệu navigation"""
    try:
        response = requests.get(BASE_URL, headers=get_headers(), timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Giả lập menu chính
        main_menu = [
            {"id": "thi-truong-chung-khoan", "name": "CHỨNG KHOÁN", "url": "/thi-truong-chung-khoan.chn"},
            {"id": "tai-chinh", "name": "TÀI CHÍNH", "url": "/tai-chinh.chn"},
            {"id": "bat-dong-san", "name": "BẤT ĐỘNG SẢN", "url": "/bat-dong-san.chn"},
            {"id": "doanh-nghiep", "name": "DOANH NGHIỆP", "url": "/doanh-nghiep.chn"}
        ]

        return {
            "mainMenu": main_menu,
            "extendedMenu": {},
            "hotTopics": ["VNM", "TCB", "HPG", "VIC", "FPT"]
        }

    except Exception as e:
        logger.error(f"Lỗi khi cào navigation: {e}")
        return {}

def search_articles(query: str, search_type: str = "news") -> List[Dict]:
    """Tìm kiếm bài viết"""
    try:
        # Giả lập tìm kiếm - trong thực tế sẽ gọi API tìm kiếm của CafeF
        all_articles = scrape_articles("thi-truong-chung-khoan", 1)
        
        # Lọc theo từ khóa
        results = []
        query_lower = query.lower()
        
        for article in all_articles:
            if (query_lower in article["title"].lower() or 
                query_lower in article["sapo"].lower()):
                results.append({
                    "id": article["id"],
                    "title": article["title"],
                    "url": article["url"]
                })
        
        return results[:10]  # Giới hạn 10 kết quả

    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm: {e}")
        return []

if __name__ == '__main__':
    # Chạy thử để kiểm tra
    scraped_articles = scrape_articles()
    if scraped_articles:
        print(f"Đã cào được {len(scraped_articles)} bài viết.")
        print("Bài viết đầu tiên:", scraped_articles[0])
