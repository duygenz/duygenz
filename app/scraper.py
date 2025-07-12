import requests
from bs4 import BeautifulSoup
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://m.cafef.vn"
TARGET_URL = f"{BASE_URL}/thi-truong-chung-khoan.chn"

def scrape_articles():
    """
    Cào dữ liệu các bài báo từ trang Thị trường chứng khoán của CafeF.

    Returns:
        list: Một danh sách các dictionary, mỗi dictionary chứa thông tin một bài báo.
              Trả về danh sách rỗng nếu có lỗi.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu status code không phải 200

        soup = BeautifulSoup(response.content, 'html.parser')
        
        list_container = soup.find('div', class_='lst')
        if not list_container:
            logger.warning("Không tìm thấy container chứa danh sách bài viết. Cấu trúc trang có thể đã thay đổi.")
            return []

        articles = []
        # Tìm tất cả các item bài viết
        article_items = list_container.find_all('div', class_='box-category-item')

        for item in article_items:
            title_tag = item.find('a', class_='item-title')
            img_tag = item.find('img')
            date_tag = item.find('div', class_='time')

            # Trích xuất thông tin, kiểm tra nếu tag tồn tại
            title = title_tag.text.strip() if title_tag else "N/A"
            link_relative = title_tag['href'] if title_tag and title_tag.has_attr('href') else ""
            
            # Tạo link tuyệt đối
            link = f"{BASE_URL}{link_relative}" if link_relative and not link_relative.startswith('http') else link_relative

            image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else ""
            published_date = date_tag.text.strip() if date_tag else "N/A"

            if title != "N/A" and link:
                articles.append({
                    "title": title,
                    "link": link,
                    "image_url": image_url,
                    "published_date": published_date,
                })
        
        return articles

    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi kết nối khi cào dữ liệu: {e}")
        return []
    except Exception as e:
        logger.error(f"Lỗi không xác định: {e}")
        return []

if __name__ == '__main__':
    # Chạy thử để kiểm tra
    scraped_articles = scrape_articles()
    if scraped_articles:
        print(f"Đã cào được {len(scraped_articles)} bài viết.")
        print("Bài viết đầu tiên:", scraped_articles[0])
