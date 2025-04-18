import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 設定（envから取得）
wp_url = os.getenv("WP_URL")
wp_username = os.getenv("WP_USERNAME")
wp_password = os.getenv("WP_PASSWORD")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Gemini初期化
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# 要約（未使用）
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def scrape_top_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ページ({url})の取得に失敗しました:", e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    article_block = soup.select_one("div.article-outer.hentry")

    if not article_block:
        print("記事ブロックが見つかりませんでした")
        return None

    date_elem = article_block.select_one(".article-date")
    title_elem = article_block.select_one(".article-header .article-title.entry-title h2")
    body_elem = article_block.select_one(".article-body.entry-content > div")

    date = date_elem.get_text(strip=True) if date_elem else "日付なし"
    title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
    body = body_elem.get_text(strip=True) if body_elem else "本文なし"

    return {
        "date": date,
        "original_title": title,
        "body": body,
        "source_url": url
    }

def clean_generated_text(text):
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
"""
        post.post_status = 'publish'
        post_id = client.call(NewPost(post))
        print(f"✅ 投稿成功（ID: {post_id}）")
        return True
    except Exception as e:
        print("❌ 投稿失敗:", e)
        return False

def main():
    url = "https://ripple.2chblog.jp/"
    print("📥 トップページ取得:", url)
    article = scrape_top_article(url)

    if not article:
        print("記事が取得できませんでした。")
        return

    print(f"📰 元タイトル: {article['original_title']}")

    # タイトル & 本文生成
    title, body = generate_title_and_article(article["original_title"], article["body"])
    article["generated_title"] = title
    article["generated_body"] = body

    print(f"✨ 生成タイトル: {title}")
    print("✅ Gemini生成完了")

    # 投稿
    post_to_wordpress_xmlrpc(article)

    print("\n🎉 投稿完了")

if __name__ == "__main__":
    main()