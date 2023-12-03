import functools
import requests
import logging

logger = logging.getLogger(__name__)

error_messages = {
    400: "Bad Request (You sent something bad)",
    403: "Not Authenticated (Token Invalid / Disabled)",
    404: "Not Found",
    408: "Request Timeout (try again, gently)",
    429: "Too Many Requests (Token quota exceeded)",
    500: "Server side issue - did you let us know?"
}

class APIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

def handle_api_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            logger.error(f"API request error: {e.status_code} {e.message}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
        except Exception as e:
            logger.error(f"An exception occurred: {e}")
    return wrapper

def check_status_code(response):
    status_code = response.status_code
    if status_code == 200:
        return status_code
    elif status_code in error_messages:
        raise APIError(status_code, error_messages[status_code])
    elif status_code in range(500, 600):
        raise APIError(status_code, error_messages[500])
    else:
        raise APIError(status_code, "Unknown error")