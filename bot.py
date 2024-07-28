from flask import Blueprint, request, jsonify
import requests
from dotenv import load_dotenv
import os
import logging
from tasks import celery_app

load_dotenv()

bot_bp = Blueprint("bot", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")


@bot_bp.route("/slack/events", methods=["POST"])
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
                # Enqueue the message processing task using Celery
                celery_app.send_task(
                    "process_message", args=[text, user_id, channel_id]
                )
                logger.info(f"Enqueued message processing task")
            except Exception as e:
                logger.error(f"Error occurred while enqueueing task: {e}")
                send_message_to_slack(
                    "Oops! Something went wrong. Please try again later.", channel_id
                )

    return jsonify({"status": "success"}), 200


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
