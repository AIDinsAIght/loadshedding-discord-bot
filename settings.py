import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import discord
import logging
from logging.config import dictConfig

load_dotenv()

# SECRETS #
DISCORD_API_SECRET = os.getenv("DISCORD_API_TOKEN")
DISCORD_CHANNEL_SECRET = int(os.getenv("DISCORD_CHANNEL_ID"))
ESP_API_SECRET = os.getenv("ESP_API_TOKEN")
GUILDS_ID_SECRET = discord.Object(id=int(os.getenv("GUILDS_ID")))

# ESP API HEADERS #
HEADERS = {'token': ESP_API_SECRET}

# SETTINGS #
FILE_PATH = 'subscriptions.pkl'
TIMEZONE = ZoneInfo('Africa/Johannesburg')

# REQUEST URLS #
URLS = {
    'api_allowance': 'https://developer.sepush.co.za/business/2.0/api_allowance',
    'area': 'https://developer.sepush.co.za/business/2.0/area?id={area}',
    'areas_search': 'https://developer.sepush.co.za/business/2.0/areas_search?text={text}',
    'eskom_status': 'https://loadshedding.eskom.co.za/LoadShedding/GetStatus',
    'status': 'https://developer.sepush.co.za/business/2.0/status',
    'test_area': 'https://developer.sepush.co.za/business/2.0/area?id={area}&test={test}'
}

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {
            "format": "%(levelname)-10s - %(name)-15s : %(message)s"
        },
    },
    "handlers": {
        "console_debug": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console_warning": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/infos.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console_debug"],
            "level": "INFO",
            "propagate": False
        },
        "discord": {
            "handlers": ["console_warning", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)