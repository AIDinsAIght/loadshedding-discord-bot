import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

# SECRETS #
DISCORD_API_SECRET = os.getenv("DISCORD_API_TOKEN")
DISCORD_CHANNEL_SECRET = int(os.getenv("DISCORD_CHANNEL_ID"))
ESP_API_SECRET = os.getenv("ESP_API_TOKEN")

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