import requests
from bs4 import BeautifulSoup
from transformers import pipeline

def get_archive_links(main_url):
    """
    メインページからアーカイブリンク一覧を取得する関数
    """
    try:
        response = requests.get(main_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print("メインページの取得に失敗しました:", e)
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    archives = []
    
    # アーカイブコンテナは id="plugin-monthly-1172541" の div 内に存在する
    archive_container = soup.find("div", id="plugin-monthly-1172541")
    if archive_container:
        for sidebody in archive_container.find_all("div", class_="sidebody"):
            a_tag = sidebody.find("a")
            if a_tag and a_tag.has_attr("href"):
                title = a_tag.get_text(strip=True)
                link = a_tag["href"]
                archives.append({
                    "title": title,
                    "link": link
                })
    else:
        print("アーカイブのコンテナが見つかりませんでした。")
    
    return archives

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
    Transformersのsummarizationパイプラインを利用して、テキストを要約する関数
    ※モデルは facebook/bart-large-cnn を利用
    """
    # 注意：初回呼び出し時にモデルのダウンロードが行われるため、少し時間がかかる場合があります
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print("要約処理でエラーが発生しました:", e)
        return "要約失敗"

def main():
    main_url = "https://ripple.2chblog.jp/"
    
    # 1. メインページからアーカイブリンク一覧を取得
    archive_links = get_archive_links(main_url)
    if not archive_links:
        print("アーカイブリンクが見つかりませんでした。")
        return
    
    print("取得したアーカイブリンク:")
    for a in archive_links:
        print(f"{a['title']} : {a['link']}")
    
    all_articles = []
    
    # 2. 各アーカイブページから記事情報を取得
    for archive in archive_links:
        print("\n--- Scraping アーカイブ:", archive["title"], "---")
        articles = scrape_archive_page(archive["link"])
        print(f"  取得した記事数: {len(articles)}")
        all_articles.extend(articles)
    
    # 3. 取得した各記事本文をAIで要約する
    for article in all_articles:
        print("\n要約前（タイトル）:", article["title"])
        # 本文が長すぎる場合は、適宜分割する必要がありますが、ここでは全文を要約に渡します
        article["summary"] = summarize_text(article["body"])
    
    # 4. 結果の表示（各記事の日付、タイトル、要約を表示）
    print("\n=== 全記事のサマリ ===")
    for article in all_articles:
        print("=" * 40)
        print("【アーカイブURL】", article["archive_url"])
        print("【日付】", article["date"])
        print("【タイトル】", article["title"])
        print("【要約】", article["summary"])
    print("=" * 40)
    print("全記事数:", len(all_articles))

if __name__ == "__main__":
    main()
