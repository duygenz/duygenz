# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import feedparser
import re

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
# Kích hoạt CORS cho tất cả các route
CORS(app)

# URL của CafeF
CAFEF_URL = "https://cafef.vn/thi-truong-chung-khoan.chn"
CAFEF_RSS_URL = "https://cafef.vn/thi-truong-chung-khoan.rss"

# --- Chức năng Scraping ---

def scrape_cafef_page():
    """
    Cào dữ liệu các bài báo nổi bật từ trang chủ thị trường chứng khoán CafeF.
    """
    try:
        response = requests.get(CAFEF_URL, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu request không thành công
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        # Tìm các bài báo trong danh sách
        news_items = soup.select("div.tlitem")

        for item in news_items:
            title_element = item.select_one("h3 a")
            image_element = item.select_one("a img")
            sapo_element = item.select_one("p.sapo")

            if title_element and title_element.has_attr('href'):
                title = title_element.get_text(strip=True)
                link = "https://cafef.vn" + title_element['href']
                image_src = image_element['src'] if image_element else None
                sapo = sapo_element.get_text(strip=True) if sapo_element else ""

                articles.append({
                    "title": title,
                    "link": link,
                    "image": image_src,
                    "description": sapo,
                    "source": "CafeF Page"
                })
        return articles
    except requests.RequestException as e:
        print(f"Lỗi khi cào trang CafeF: {e}")
        return []

def parse_cafef_rss():
    """
    Phân tích dữ liệu từ RSS feed của CafeF.
    """
    try:
        feed = feedparser.parse(CAFEF_RSS_URL)
        articles = []

        for entry in feed.entries:
            # Sử dụng regex để trích xuất URL ảnh từ CDATA
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
        return articles
    except Exception as e:
        print(f"Lỗi khi phân tích RSS: {e}")
        return []

# --- Định nghĩa các Route API ---

@app.route('/')
def home():
    """
    Route chào mừng.
    """
    return jsonify({
        "message": "Chào mừng đến với API Tin tức Chứng khoán CafeF!",
        "endpoints": {
            "/api/news": "Lấy tất cả tin tức từ trang web và RSS.",
            "/api/page": "Chỉ lấy tin tức từ trang web CafeF.",
            "/api/rss": "Chỉ lấy tin tức từ RSS feed."
        }
    })

@app.route('/api/news')
def get_all_news():
    """
    Lấy và kết hợp tin tức từ cả hai nguồn.
    """
    page_news = scrape_cafef_page()
    rss_news = parse_cafef_rss()

    # Kết hợp và loại bỏ trùng lặp (dựa trên link)
    all_news = rss_news
    seen_links = {item['link'] for item in rss_news}

    for item in page_news:
        if item['link'] not in seen_links:
            all_news.append(item)
            seen_links.add(item['link'])

    if not all_news:
        return jsonify({"error": "Không thể lấy dữ liệu từ CafeF."}), 500

    return jsonify(all_news)

@app.route('/api/page')
def get_page_news():
    """
    Chỉ lấy tin tức từ cào trang web.
    """
    news = scrape_cafef_page()
    if not news:
        return jsonify({"error": "Không thể cào dữ liệu từ trang CafeF."}), 500
    return jsonify(news)

@app.route('/api/rss')
def get_rss_news():
    """
    Chỉ lấy tin tức từ RSS feed.
    """
    news = parse_cafef_rss()
    if not news:
        return jsonify({"error": "Không thể phân tích RSS feed."}), 500
    return jsonify(news)

# Chạy ứng dụng
if __name__ == '__main__':
    # Port được Render tự động gán qua biến môi trường PORT
    app.run(host='0.0.0.0', port=5000)

