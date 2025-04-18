import requests
from bs4 import BeautifulSoup

BASE_URL = "https://bittimes.net/"  # ← 一覧ページのURLをここに入れてください

def get_latest_article_url(base_url):
    res = requests.get(base_url)
    soup = BeautifulSoup(res.content, "html.parser")

    first_a_tag = soup.select_one(".thumb-text-list-posts a")
    if not first_a_tag or not first_a_tag.get("href"):
        raise Exception("記事のURLが見つかりませんでした。")

    href = first_a_tag["href"]
    # 相対URLを絶対URLに変換
    if href.startswith("/"):
        href = base_url.rstrip("/") + href

    return href

def extract_text_from_article(article_url):
    res = requests.get(article_url)
    soup = BeautifulSoup(res.content, "html.parser")

    # h1, h2, p タグのテキストを取得
    tags = soup.find_all(['h1', 'h2', 'p'])

    print("✅ 記事内のテキスト:")
    for tag in tags:
        text = tag.get_text(strip=True)
        if text:
            print(text)

if __name__ == "__main__":
    try:
        article_url = get_latest_article_url(BASE_URL)
        print("📰 最新記事のURL:", article_url)
        extract_text_from_article(article_url)
    except Exception as e:
        print("❌ エラー:", e)
