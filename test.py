import os
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from dotenv import load_dotenv

# .envファイルからWordPressの設定を読み込み（未設定の場合は直接記述も可能）
load_dotenv()
WP_API_URL = os.getenv("WP_API_URL", "http://bottest.local/")  # ここを実際のサイトURLに変更
WP_USERNAME = os.getenv("WP_USERNAME", "root")
WP_PASSWORD = os.getenv("WP_PASSWORD", "root")

def scrape_archive_page(archive_url):
    """
    指定されたアーカイブページから、各記事の日付、タイトル、本文を取得する関数
    """
    try:
        response = requests.get(archive_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"アーカイブページ({archive_url})の取得に失敗しました:", e)
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # 各記事ブロックは "article-outer hentry" クラスを持つdiv内にある
    article_blocks = soup.select("div.article-outer.hentry")
    if not article_blocks:
        print(f"記事ブロックが見つかりませんでした: {archive_url}")
    
    for block in article_blocks:
        # 日付（class="article-date"）
        date_elem = block.select_one(".article-date")
        date_text = date_elem.get_text(strip=True) if date_elem else "日付なし"
        
        # タイトル（h2タグ内のclass="article-title entry-title"）
        title_elem = block.select_one("h2.article-title.entry-title")
        title_text = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
        
        # 本文（divタグ内のclass="article-body entry-content"）
        body_elem = block.select_one("div.article-body.entry-content")
        body_text = body_elem.get_text(strip=True) if body_elem else "本文なし"
        
        articles.append({
            "date": date_text,
            "title": title_text,
            "body": body_text,
            "archive_url": archive_url
        })
    
    return articles

def summarize_text(text, max_length=150, min_length=40):
    """
    Transformersのsummarizationパイプラインを利用してテキストを要約する関数
    ※初回実行時はモデルのダウンロードに時間がかかる場合があります
    """
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print("要約処理でエラーが発生しました:", e)
        return "要約失敗"

def post_to_wordpress(article, wp_api_url, username, password):
    """
    WordPress REST API を利用して記事を投稿する関数
    ※WordPress側で REST API が有効で、認証が利用できる状態である必要があります
    """
    endpoint = f"{wp_api_url}/wp-json/wp/v2/posts"
    headers = {"Content-Type": "application/json"}
    data = {
        "title": article["title"],
        "content": f"<p>{article['body']}</p><hr><p><strong>要約:</strong> {article.get('summary', '')}</p>",
        "status": "publish"
    }
    try:
        response = requests.post(endpoint, headers=headers, auth=(username, password), json=data)
        response.raise_for_status()
        post_url = response.json().get("link", "URLなし")
        print(f"投稿成功: {post_url}")
        return True
    except requests.RequestException as e:
        response_text = ""
        if hasattr(e, "response") and e.response is not None:
            response_text = e.response.text
        print("WordPressへの投稿に失敗しました:", e, response_text)
        return False

def main():
    # テスト対象のアーカイブURL（2025年03月）
    archive_url = "https://ripple.2chblog.jp/archives/2025-03.html"
    print("【テスト対象アーカイブ】", archive_url)
    
    # 1. 指定アーカイブページから記事情報を取得
    articles = scrape_archive_page(archive_url)
    print(f"取得した記事数: {len(articles)}")
    
    if not articles:
        print("記事が見つかりませんでした。")
        return
    
    # 2. 各記事本文をAIで要約する
    for article in articles:
        print(f"\n要約処理中（タイトル）: {article['title']}")
        article["summary"] = summarize_text(article["body"])
    
    # 3. 取得した記事をWordPressに自動投稿する
    for article in articles:
        print(f"\nWordPressに投稿中（タイトル）: {article['title']}")
        post_to_wordpress(article, WP_API_URL, WP_USERNAME, WP_PASSWORD)
    
    print("\n=== 投稿処理完了 ===")
    print("全記事数:", len(articles))

if __name__ == "__main__":
    main()
