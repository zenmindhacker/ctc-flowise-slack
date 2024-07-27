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
        user_id = slack_event["event"]["user"]
        user_message = slack_event["event"]["text"]
        channel_id = slack_event["event"]["channel"]

        # Generate a unique session ID for the user
        session_id = f"slack_{user_id}"

        # Process the user's message and generate a response
        response_text = process_message(user_message, session_id)

        # Send the response back to Slack
        send_message_to_slack(response_text, channel_id)

    return jsonify({"challenge": slack_event.get("challenge")}), 200


def process_message(message, session_id):
    headers = {"Authorization": f"Bearer {FLOWISE_API_KEY}"}
    payload = {
        "question": message,
        "sessionId": session_id,
        "memoryKey": "buffer_memory",
    }

    response = requests.post(FLOWISE_API_URL, headers=headers, json=payload)
    response_data = response.json()

    chatbot_response = response_data["data"]["output"]

    return chatbot_response


def send_message_to_slack(message, channel_id):
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    payload = {"channel": channel_id, "text": message}

    response = requests.post(
        "https://slack.com/api/chat.postMessage", headers=headers, json=payload
    )


if __name__ == "__main__":
    app.run()
