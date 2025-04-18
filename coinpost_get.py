import requests
from bs4 import BeautifulSoup
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import google.generativeai as genai
import os
from dotenv import load_dotenv

# ====== .envから設定を読み込み ======
load_dotenv()
wp_url         = os.getenv("WP_URL")
wp_username    = os.getenv("WP_USERNAME")
wp_password    = os.getenv("WP_PASSWORD")
gemini_api_key = os.getenv("GEMINI_API_KEY")
# ====================================

# 1) トップページから最新記事リンクを取得
HOME_URL = "https://coinpost.jp/"
resp = requests.get(HOME_URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

link_tag = soup.select_one(".hmml-list .homelist-in:first-of-type .homelist-in-text a")
if not link_tag or not link_tag.has_attr("href"):
    print("❌ 記事URLが取得できませんでした")
    exit(1)
article_url = link_tag["href"]
print("✅ 取得した記事URL:", article_url)

# 2) 記事ページからタイトルと本文を取得
resp = requests.get(article_url)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

title_tag = soup.select_one(".entry-content h1")
title = title_tag.get_text(strip=True) if title_tag else "（タイトル取得失敗）"

paras = soup.select(".entry-content p")
body = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))
if not body:
    print("❌ 記事本文が取得できませんでした")
    exit(1)

# 3) Gemini でリライト
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

prompt = f"""\
次のCoinPost記事を、仮想通貨初心者にもわかりやすい「です・ます調」で再構成し、
・新しいタイトルをつける
・本文末尾に元記事リンクをHTMLの<a>タグで追加する

元記事タイトル：{title}
元記事URL：{article_url}

記事内容：
{body}
"""

response = model.generate_content(prompt)
lines = response.text.strip().splitlines()
gen_title = lines[0]
gen_body  = "\n".join(lines[1:]) + f'\n\n<p><a href="{article_url}" target="_blank">元記事はこちら</a></p>'

# 4) WordPress に投稿
wp = Client(wp_url, wp_username, wp_password)
post = WordPressPost()
post.title       = gen_title
post.content     = gen_body
post.post_status = 'publish'

try:
    post_id = wp.call(NewPost(post))
    print(f"✅ 投稿成功！投稿ID: {post_id}")
except Exception as e:
    print("❌ 投稿失敗:", e)