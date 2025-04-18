from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

# あなたのローカルWPサイトのURLとログイン情報
wp_url = "http://bottest.local/xmlrpc.php"  # Local by Flywheel のURLに合わせて変更
wp_username = "root"
wp_password = "root"

# クライアント作成
client = Client(wp_url, wp_username, wp_password)

# 接続確認（オプション）
user = client.call(GetUserInfo())
print(f"✅ ログイン成功：{user.username}")

# 投稿作成
post = WordPressPost()
post.title = "テスト投稿 from Pythoddn"
post.content = "これはPythonスクリプトから投稿されたテスト記事です。"
post.post_status = 'publish'  # 公開。ドラフトなら 'draft'

# 投稿送信
post_id = client.call(NewPost(post))
print(f"✅ 投稿成功！投稿ID: {post_id}")
