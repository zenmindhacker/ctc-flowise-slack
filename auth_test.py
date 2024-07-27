import os
import requests
from dotenv import load_dotenv

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
response = requests.get(
    "https://slack.com/api/auth.test",
    headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
)
user_id = response.json()["user_id"]
print(f"Bot User ID: {user_id}")
