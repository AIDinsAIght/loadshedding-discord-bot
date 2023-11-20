import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_API_SECRET = os.getenv("DISCORD_API_TOKEN")
DISCORD_CHANNEL_SECRET = os.getenv("DISCORD_CHANNEL_ID")
ESP_API_SECRET = os.getenv("ESP_API_TOKEN")