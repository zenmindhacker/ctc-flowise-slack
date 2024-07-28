import os
import requests
from celery import Celery
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

celery_app = Celery("tasks", broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)

FLOWISE_API_URL = os.getenv("FLOWISE_API_URL")
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")

session_ids = {}  # Dictionary to store session IDs for each user and channel


@celery_app.task(name="process_message")
def process_message(message, user_id, channel_id):
    try:
        # Check if the message is from the bot itself
        if user_id == SLACK_BOT_USER_ID:
            logger.info("Message is from the bot itself. Ignoring.")
            return

        # Generate a unique session ID for the user and channel combination
        session_id = f"slack_{user_id}_{channel_id}"

        headers = {"Authorization": f"Bearer {FLOWISE_API_KEY}"}
        payload = {
            "question": message,
            "sessionId": session_id,
            "memoryKey": "buffer_memory",
        }
        logger.info(f"Sending request to Flowise API with payload: {payload}")

        response = requests.post(FLOWISE_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        response_data = response.json()
        logger.info(f"Received response from Flowise API: {response_data}")

        # Extract the session ID from the API response
        session_id = response_data.get("sessionId")
        if session_id:
            session_ids[(user_id, channel_id)] = session_id
            logger.info(f"Extracted session ID: {session_id}")
        else:
            logger.warning("Session ID not found in the API response")

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
