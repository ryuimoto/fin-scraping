import tweepy
import os
from dotenv import load_dotenv

# .envから読み込む
load_dotenv()
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# 認証
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# 投稿内容
tweet = "これはPythonから自動投稿したテストツイートです！🚀"

# 投稿
try:
    api.update_status(tweet)
    print("✅ 投稿成功！")
except Exception as e:
    print("❌ 投稿失敗:", e)
