import os
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from dotenv import load_dotenv
import google.generativeai as genai

# .envファイルから設定読み込み
load_dotenv()
WP_API_URL = os.getenv("WP_API_URL", "http://bottest.local/")
WP_USERNAME = os.getenv("WP_USERNAME", "root")
WP_PASSWORD = os.getenv("WP_PASSWORD", "root")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini設定
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Transformers summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def scrape_archive_page(archive_url):
    try:
        response = requests.get(archive_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"アーカイブページ({archive_url})の取得に失敗しました:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    article_blocks = soup.select("div.article-outer.hentry")
    if not article_blocks:
        print(f"記事ブロックが見つかりませんでした: {archive_url}")

    for block in article_blocks:
        date_elem = block.select_one(".article-date")
        title_elem = block.select_one("h2.article-title.entry-title")
        body_elem = block.select_one("div.article-body.entry-content")

        date = date_elem.get_text(strip=True) if date_elem else "日付なし"
        title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
        body = body_elem.get_text(strip=True) if body_elem else "本文なし"

        articles.append({
            "date": date,
            "title": title,
            "body": body
        })

    return articles

def summarize_text(text, max_length=150, min_length=40):
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print("要約失敗:", e)
        return "要約エラー"

def generate_with_gemini(title, original_text):
    prompt = f"""
以下のタイトルと内容をもとに、新たなブログ記事を自然な日本語で生成してください。

【タイトル】
{title}

【元記事の内容】
{original_text}

【生成条件】
・日本語で書いてください。
・見出しや段落を使って読みやすく。
・口調はやさしく、丁寧に。
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini生成失敗:", e)
        return "生成エラー"

def main():
    archive_url = "https://ripple.2chblog.jp/archives/2025-03.html"
    print("【テスト対象アーカイブ】", archive_url)

    articles = scrape_archive_page(archive_url)
    print(f"取得した記事数: {len(articles)}")

    if not articles:
        print("記事が見つかりませんでした。")
        return

    for i, article in enumerate(articles):
        print(f"\n========== 記事 {i+1} ==========")
        print(f"📅 日付: {article['date']}")
        print(f"📰 タイトル: {article['title']}")
        print(f"🗒️ 本文（冒頭100字）: {article['body'][:100]}...")

        # 要約
        print("\n🔍 要約中...")
        summary = summarize_text(article["body"])
        article["summary"] = summary
        print(f"📝 要約:\n{summary}")

        # Gemini生成
        print("\n✨ Geminiによる生成中...")
        generated = generate_with_gemini(article["title"], article["body"])
        article["generated"] = generated
        print(f"\n🧠 Gemini生成結果:\n{generated}")

    print("\n=== 全処理完了 ===")

if __name__ == "__main__":
    main()
