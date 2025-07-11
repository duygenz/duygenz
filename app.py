# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import feedparser
import re
import logging

# Cấu hình logging để dễ dàng gỡ lỗi trên Render
logging.basicConfig(level=logging.INFO)

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
# Kích hoạt CORS cho tất cả các route, an toàn hơn cho sản phẩm
CORS(app, resources={r"/api/*": {"origins": "*"}})

# URL của CafeF
CAFEF_URL = "https://cafef.vn/thi-truong-chung-khoan.chn"
CAFEF_RSS_URL = "https://cafef.vn/thi-truong-chung-khoan.rss"

# --- Chức năng Scraping ---

def scrape_cafef_page():
    """
    Cào dữ liệu các bài báo nổi bật từ trang chủ thị trường chứng khoán CafeF.
    Trả về một tuple: (success, data)
    """
    try:
        logging.info("Bắt đầu cào dữ liệu từ trang web CafeF...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(CAFEF_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        news_items = soup.select("div.tlitem")

        if not news_items:
            logging.warning("Không tìm thấy mục tin tức nào với selector 'div.tlitem'")
            return (True, []) # Trả về thành công nhưng không có dữ liệu

        for item in news_items:
            title_element = item.select_one("h3 a")
            image_element = item.select_one("a img")
            sapo_element = item.select_one("p.sapo")

            if title_element and title_element.has_attr('href'):
                title = title_element.get_text(strip=True)
                link = "https://cafef.vn" + title_element['href']
                image_src = image_element['src'] if image_element and image_element.has_attr('src') else None
                sapo = sapo_element.get_text(strip=True) if sapo_element else ""

                articles.append({
                    "title": title,
                    "link": link,
                    "image": image_src,
                    "description": sapo,
                    "source": "CafeF Page"
                })
        logging.info(f"Cào thành công {len(articles)} bài báo từ trang web.")
        return (True, articles)
    except requests.RequestException as e:
        logging.error(f"Lỗi Request khi cào trang CafeF: {e}")
        return (False, f"Lỗi kết nối đến CafeF: {e}")
    except Exception as e:
        logging.error(f"Lỗi không xác định khi cào trang CafeF: {e}")
        return (False, f"Lỗi máy chủ nội bộ khi cào dữ liệu: {e}")


def parse_cafef_rss():
    """
    Phân tích dữ liệu từ RSS feed của CafeF.
    Trả về một tuple: (success, data)
    """
    try:
        logging.info("Bắt đầu phân tích RSS feed...")
        feed = feedparser.parse(CAFEF_RSS_URL)
        
        if feed.bozo:
            logging.warning(f"RSS feed có thể bị lỗi: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries:
            image_match = re.search(r'src="([^"]+)"', entry.summary)
            image_url = image_match.group(1) if image_match else None

            articles.append({
                "title": entry.title,
                "link": entry.link,
                "image": image_url,
                "description": entry.summary_detail.get('value', ''),
                "published": entry.published,
                "source": "CafeF RSS"
            })
        logging.info(f"Phân tích thành công {len(articles)} bài báo từ RSS.")
        return (True, articles)
    except Exception as e:
        logging.error(f"Lỗi khi phân tích RSS: {e}")
        return (False, f"Lỗi máy chủ nội bộ khi phân tích RSS: {e}")

# --- Định nghĩa các Route API ---

@app.route('/')
def home():
    return jsonify({
        "message": "Chào mừng đến với API Tin tức Chứng khoán CafeF! (v2)",
        "status": "online"
    })

@app.route('/api/news')
def get_all_news():
    logging.info("Nhận được yêu cầu tới /api/news")
    success_page, data_page = scrape_cafef_page()
    success_rss, data_rss = parse_cafef_rss()

    if not success_page and not success_rss:
        return jsonify({"error": "Không thể lấy dữ liệu từ cả hai nguồn.", "details": [data_page, data_rss]}), 502

    all_news = data_rss if success_rss else []
    page_news = data_page if success_page else []
    
    seen_links = {item['link'] for item in all_news}

    for item in page_news:
        if item['link'] not in seen_links:
            all_news.append(item)
            seen_links.add(item['link'])
    
    if not all_news:
         return jsonify({"error": "Không tìm thấy bài báo nào."}), 404

    return jsonify(all_news)

# Chạy ứng dụng
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)