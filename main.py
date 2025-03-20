# import requests
# from bs4 import BeautifulSoup

# def get_archive_links(url="https://ripple.2chblog.jp/"):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # HTTPエラーの場合例外発生
#     except requests.RequestException as e:
#         print("ページの取得に失敗しました:", e)
#         return []

#     # BeautifulSoupでHTMLをパース（パーサーはhtml.parserを使用）
#     soup = BeautifulSoup(response.text, "html.parser")
    
#     archives = []
#     # アーカイブのコンテナは id="plugin-monthly-1172541" の div 内
#     archive_container = soup.find("div", id="plugin-monthly-1172541")
#     if archive_container:
#         # 各アーカイブは div.sidebody 内の <a> タグに存在する
#         for sidebody in archive_container.find_all("div", class_="sidebody"):
#             a_tag = sidebody.find("a")
#             if a_tag and a_tag.has_attr("href"):
#                 title = a_tag.get_text(strip=True)
#                 link = a_tag["href"]
#                 archives.append({
#                     "title": title,
#                     "link": link
#                 })
#     else:
#         print("アーカイブのコンテナが見つかりませんでした。")
    
#     return archives

# if __name__ == "__main__":
#     archive_links = get_archive_links()
#     if archive_links:
#         print("取得したアーカイブリンク:")
#         for archive in archive_links:
#             print(f"{archive['title']} : {archive['link']}")
#     else:
#         print("アーカイブリンクは見つかりませんでした。")


import requests
from bs4 import BeautifulSoup

def scrape_archive_page(archive_url):
    try:
        response = requests.get(archive_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print("アーカイブページの取得に失敗しました:", e)
        return []
    
    # HTMLをパース
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # 各記事ブロックは "article-outer hentry" クラスを持つdiv内に存在する
    article_blocks = soup.select("div.article-outer.hentry")
    if not article_blocks:
        print("記事ブロックが見つかりませんでした。")
    
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

if __name__ == "__main__":
    # 例として2025年3月のアーカイブページURL
    archive_url = "https://ripple.2chblog.jp/archives/2025-03.html"
    article_data = scrape_archive_page(archive_url)
    
    # 取得結果の表示（本文は先頭200文字のみ表示）
    for art in article_data:
        print("【日付】", art["date"])
        print("【タイトル】", art["title"])
        print("【本文（先頭200文字）】", art["body"][:1000])
        print("="*40)
