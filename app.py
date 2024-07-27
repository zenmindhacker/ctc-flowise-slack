from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
FLOWISE_API_URL = os.getenv("FLOWISE_API_URL")
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY")


@app.route("/slack/events", methods=["POST"])
def slack_events():
    slack_event = request.json

    if slack_event["type"] == "app_mention" or slack_event["type"] == "message":
        user_message = slack_event["event"]["text"]
        channel_id = slack_event["event"]["channel"]

        # Process the user's message and generate a response
        response_text = process_message(user_message)

        # Send the response back to Slack
        send_message_to_slack(response_text, channel_id)

    return jsonify({"challenge": slack_event.get("challenge")}), 200


def process_message(message):
    headers = {"Authorization": f"Bearer {FLOWISE_API_KEY}"}
    payload = {"text": message}

    response = requests.post(FLOWISE_API_URL, headers=headers, json=payload)
    chatbot_response = response.json()["data"]["output"]

    return chatbot_response


def send_message_to_slack(message, channel_id):
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    payload = {"channel": channel_id, "text": message}

    response = requests.post(
        "https://slack.com/api/chat.postMessage", headers=headers, json=payload
    )


if __name__ == "__main__":
    app.run()
