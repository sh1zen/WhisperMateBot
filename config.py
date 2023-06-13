import configparser
from os import getenv

config = configparser.ConfigParser()
config.read("./config/config.ini")

""" General config """
# Set ENV to any value to use webhook instead of polling for bot. Must be set in prod environment.
ENV = getenv("ENV")
TZ_OFFSET = 1.0  # (UTC+01:00)
JOB_LIMIT_PER_PERSON = 10
BOT_NAME = 'WhisperMate'
BOT_NAME_FULL = 'WhisperMateBot'


""" Telegram config """
TELEGRAM_BOT_TOKEN = config["KEYS"]["bot_api"]
BOT_HOST = getenv("BOTHOST")  # only required in prod environment


