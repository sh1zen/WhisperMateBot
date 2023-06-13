import json
import os
from urllib.parse import urlencode

import requests

from config import TELEGRAM_BOT_TOKEN


def get_bot_details(user_bot_token):
    endpoint = "https://api.telegram.org/bot{}/getMe".format(user_bot_token)
    return requests.get(endpoint)


def send_media_group(chat_id, photo_id, content, user_bot_token):
    media, files = prepare_photos(photo_id, content)
    query_string = urlencode({"chat_id": chat_id, "media": media})
    endpoint = "https://api.telegram.org/bot{}/sendMediaGroup?{}".format(
        user_bot_token, query_string
    )
    return requests.post(endpoint, files=files)


def send_single_photo(chat_id, photo_id, content, user_bot_token):
    query = {
        "chat_id": chat_id,
        "photo": photo_id,
        "caption": content,
        "parse_mode": "html",
    }
    query_string = urlencode(query)
    endpoint = "https://api.telegram.org/bot{}/sendPhoto?{}".format(
        user_bot_token, query_string
    )
    return requests.get(endpoint)


def send_poll(chat_id, content, user_bot_token):
    poll_content = json.loads(content)
    endpoint = "https://api.telegram.org/bot{}/sendPoll".format(user_bot_token)
    parameters = {
        "chat_id": chat_id,
        "question": poll_content.get("question"),
        "options": json.dumps(
            [option.get("text") for option in poll_content.get("options")]
        ),
        "type": poll_content.get("type"),
        "is_anonymous": poll_content.get("is_anonymous"),
        "allows_multiple_answers": poll_content.get("allows_multiple_answers"),
        "correct_option_id": poll_content.get("correct_option_id"),
        "explanation": poll_content.get("explanation"),
        "explanation_parse_mode": "html",
        "is_closed": poll_content.get("is_closed"),
        "close_date": poll_content.get("close_date"),
    }
    return requests.get(endpoint, data=parameters)


def send_text(chat_id, content):
    query = {"chat_id": chat_id, "text": content, "parse_mode": "html"}
    query_string = urlencode(query)
    endpoint = "https://api.telegram.org/bot{}/sendMessage?{}".format(
        TELEGRAM_BOT_TOKEN, query_string
    )
    return requests.get(endpoint)


def delete_message(chat_id, previous_message_id):
    response = False

    for message_id in previous_message_id.split(";"):
        endpoint = "https://api.telegram.org/bot{}/deleteMessage?chat_id={}&message_id={}".format(
            TELEGRAM_BOT_TOKEN, chat_id, message_id
        )
        response = requests.get(endpoint)
    return response.json()["ok"] if response else False


def prepare_photos(photo_id, content):
    photo_ids = photo_id.split(";")
    media, files = [], {}
    for i, photo_id in enumerate(photo_ids):
        files = download_photo(files, photo_id)
        media.append(
            {
                "type": "photo",
                "media": "attach://%s" % photo_id,
                "caption": content if i <= 0 else "",
            }
        )
    return json.dumps(media), files


def download_photo(files, photo_id):
    file_details_endpoint = "https://api.telegram.org/bot{}/getFile?file_id={}".format(
        TELEGRAM_BOT_TOKEN, photo_id
    )
    file_details_response = requests.get(file_details_endpoint)
    file_path = file_details_response.json()["result"]["file_path"]
    file_url = "https://api.telegram.org/file/bot{}/{}".format(TELEGRAM_BOT_TOKEN, file_path)
    file_response = requests.get(file_url)
    open(photo_id, "wb").write(file_response.content)
    files[photo_id] = open(photo_id, "rb")
    os.remove(photo_id)
    return files
