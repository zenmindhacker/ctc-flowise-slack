from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os
import logging
from flask_rq2 import RQ

load_dotenv()

app = Flask(__name__)
app.config["RQ_REDIS_URL"] = os.getenv("REDIS_URL")
rq = RQ(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
FLOWISE_API_URL = os.getenv("FLOWISE_API_URL")
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")


@app.route("/slack/events", methods=["POST"])
def slack_events():
    slack_event = request.json
    logger.info(f"Received Slack event: {slack_event}")

    if slack_event.get("type") == "url_verification":
        return jsonify({"challenge": slack_event.get("challenge")})

    if slack_event.get("type") == "event_callback":
        event_data = slack_event.get("event")
        if (
            event_data.get("type") == "app_mention"
            or event_data.get("type") == "message"
        ):
            user_id = event_data.get("user")
            text = event_data.get("text")
            channel_id = event_data.get("channel")
            logger.info(
                f"Received message from user {user_id} in channel {channel_id}: {text}"
            )

            try:
                # Enqueue the message processing job
                rq.get_queue().enqueue(process_message, text, user_id, channel_id)
                logger.info(f"Enqueued message processing job")
            except Exception as e:
                logger.error(f"Error occurred while enqueueing job: {e}")
                send_message_to_slack(
                    "Oops! Something went wrong. Please try again later.", channel_id
                )

    return jsonify({"status": "success"}), 200


@rq.job
def process_message(message, user_id, channel_id):
    try:
        # Check if the message is from the bot itself
        if user_id == SLACK_BOT_USER_ID:
            logger.info("Message is from the bot itself. Ignoring.")
            return

        headers = {"Authorization": f"Bearer {FLOWISE_API_KEY}"}
        payload = {
            "question": message,
            "sessionId": f"slack_{user_id}",
            "memoryKey": "buffer_memory",
        }
        logger.info(f"Sending request to Flowise API: {payload}")

        response = requests.post(FLOWISE_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        response_data = response.json()
        logger.info(f"Received response from Flowise API: {response_data}")

        chatbot_response = response_data["text"]
        send_message_to_slack(chatbot_response, channel_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error occurred while processing message: {e}")
        send_message_to_slack(
            "Oops! Something went wrong. Please try again later.", channel_id
        )


def send_message_to_slack(message, channel_id):
    try:
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        payload = {"channel": channel_id, "text": message}
        logger.info(f"Sending message to Slack: {payload}")

        response = requests.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload
        )
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        logger.info(f"Message sent to Slack successfully")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error occurred while sending message to Slack: {e}")


if __name__ == "__main__":
    app.run()
