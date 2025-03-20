import requests
from bs4 import BeautifulSoup
from transformers import pipeline

def scrape_archive_page(archive_url):
    """
    指定されたアーカイブページから、各記事の
    日付、タイトル、本文を取得する関数
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
            "body": body_text
        })
    
    return articles

def summarize_text_jp(text, max_length=150, min_length=40):
    """
    日本語対応のT5モデル「sonoisa/t5-base-japanese」を用いてテキストを要約する関数。
    ※T5では、入力テキストの先頭にタスクを示すプロンプト（ここでは「要約: 」）を付与する必要があります。
    """
    # モデルとトークナイザーを指定
    summarizer = pipeline("summarization", model="sonoisa/t5-base-japanese", tokenizer="sonoisa/t5-base-japanese")
    # 入力文の先頭に「要約: 」を追加
    input_text = "要約: " + text
    try:
        summary = summarizer(input_text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print("要約処理でエラーが発生しました:", e)
        return "要約失敗"

def main():
    # テスト対象は「2025年03月」のアーカイブページ
    archive_url = "https://ripple.2chblog.jp/archives/2025-03.html"
    print("スクレイピング対象のアーカイブページ:", archive_url)
    
    articles = scrape_archive_page(archive_url)
    if not articles:
        print("記事が見つかりませんでした。")
        return
    
    print(f"取得した記事数: {len(articles)}")
    
    # 各記事に対して日本語で要約処理を実施
    for idx, article in enumerate(articles, start=1):
        print("\n" + "=" * 40)
        print(f"【記事 {idx}】")
        print("【日付】", article["date"])
        print("【タイトル】", article["title"])
        print("【本文（先頭200文字）】", article["body"][:200])
        
        summary = summarize_text_jp(article["body"])
        print("【要約】", summary)

if __name__ == "__main__":
    main()
