import requests
from bs4 import BeautifulSoup
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import json
import os
from dotenv import load_dotenv

# ====== .env 読み込み ======
load_dotenv()
list_page_url   = "https://bittimes.net/"
wp_url          = os.getenv("WP_URL")
wp_username     = os.getenv("WP_USERNAME")
wp_password     = os.getenv("WP_PASSWORD")
gemini_api_key  = os.getenv("GEMINI_API_KEY")
gemini_api_url  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
# ===========================

# ① 最新記事のURLを取得
res = requests.get(list_page_url)
soup = BeautifulSoup(res.text, "html.parser")
first_a = soup.select_one(".thumb-text-list-posts a")
if not first_a:
    raise Exception("記事のURLが見つかりません")
article_url = first_a.get("href")
print("✅ 取得した記事URL:", article_url)

# ② 記事本文を取得
res = requests.get(article_url)
article_soup = BeautifulSoup(res.text, "html.parser")

elements = article_soup.select("h1, h2, p")
text_content = "\n".join([el.get_text(strip=True) for el in elements])
print("📝 取得したテキスト:\n", text_content)

# ③ Gemini で要約・記事生成
headers = {
    "Content-Type": "application/json"
}
data = {
    "contents": [{
        "parts": [{"text": f"以下の内容を元に、仮想通貨に関する読みやすいブログ記事を生成してください。\n\n{text_content}"}]
    }]
}
params = {"key": gemini_api_key}
response = requests.post(gemini_api_url, headers=headers, params=params, json=data)
response_json = response.json()
generated_text = response_json['candidates'][0]['content']['parts'][0]['text']

print("✨ Geminiで生成した記事:\n", generated_text)

# ④ WordPress に投稿（タイトルは1行目、本文は残り）
lines = generated_text.strip().splitlines()
title = lines[0]
body = "\n".join(lines[1:])

client = Client(wp_url, wp_username, wp_password)
post = WordPressPost()
post.title = title
post.content = body
post.post_status = 'publish'

post_id = client.call(NewPost(post))
print(f"✅ 投稿完了！Post ID: {post_id}")