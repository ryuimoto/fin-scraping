# 現状完成形

import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import google.generativeai as genai
import re

# 設定
wp_url = "http://bottest.local/xmlrpc.php"
wp_username = "root"
wp_password = "root"
gemini_api_key = "AIzaSyDPPt9BASSongNilmj_kMJ6lSBjckvHCVQ"

# Gemini初期化
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# 要約（未使用になっているが残しておく場合）
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

    for block in article_blocks:
        date_elem = block.select_one(".article-date")
        title_elem = block.select_one("h2.article-title.entry-title")
        body_elem = block.select_one("div.article-body.entry-content")

        date = date_elem.get_text(strip=True) if date_elem else "日付なし"
        title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
        body = body_elem.get_text(strip=True) if body_elem else "本文なし"

        articles.append({
            "date": date,
            "original_title": title,
            "body": body,
            "source_url": archive_url
        })

    return articles

def clean_generated_text(text):
    """
    BOBGリンクや宣伝文を削除
    """
    text = re.sub(r"BOBGについて.*?https?://\S+", "", text, flags=re.DOTALL)
    return text.strip()

def generate_title_and_article(original_title, body):
    prompt = f"""
以下の内容をもとに、ブログ記事とそのタイトルを日本語で作成してください。

【元タイトル】
{original_title}

【本文】
{body}

【条件】
・タイトルや本文に##といったテキストは不要
・まず最初に記事タイトルを1行で書いてください（32文字以内が理想）
・次にそのタイトルに合った自然な日本語の本文を出力してください
・本文は見出しや段落を含めて読みやすくしてください
・宣伝文やリンクは含めないでください
"""
    try:
        response = gemini_model.generate_content(prompt)
        full_text = clean_generated_text(response.text)
        lines = full_text.strip().split('\n', 1)
        generated_title = lines[0].strip()
        generated_body = lines[1].strip() if len(lines) > 1 else "本文生成失敗"
        return generated_title, generated_body
    except Exception as e:
        print("Gemini生成失敗:", e)
        return "タイトル生成エラー", "本文生成エラー"

def post_to_wordpress_xmlrpc(article):
    try:
        client = Client(wp_url, wp_username, wp_password)
        post = WordPressPost()
        post.title = article["generated_title"]
        post.content = f"""
<p>{article['generated_body'].replace('\n', '<br>')}</p>
<hr>
<p><a href="{article['source_url']}" target="_blank" rel="noopener noreferrer">▶ 参考記事を読む</a></p>
"""
        post.post_status = 'publish'
        post_id = client.call(NewPost(post))
        print(f"✅ 投稿成功（ID: {post_id}）")
        return True
    except Exception as e:
        print("❌ 投稿失敗:", e)
        return False

def main():
    archive_url = "https://ripple.2chblog.jp/archives/2025-03.html"
    print("📥 アーカイブ取得:", archive_url)
    articles = scrape_archive_page(archive_url)

    if not articles:
        print("記事が見つかりませんでした。")
        return

    for i, article in enumerate(articles):
        print(f"\n=== 記事 {i+1} / {len(articles)} ===")
        print(f"📰 元タイトル: {article['original_title']}")

        # タイトル & 本文生成
        title, body = generate_title_and_article(article["original_title"], article["body"])
        article["generated_title"] = title
        article["generated_body"] = body

        print(f"✨ 生成タイトル: {title}")
        print("✅ Gemini生成完了")

        # 投稿
        post_to_wordpress_xmlrpc(article)

    print("\n🎉 全投稿完了")

if __name__ == "__main__":
    main()
