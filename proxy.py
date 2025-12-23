from telegram.request import HTTPXRequest
from config import PROXY_URL

def get_request():
    if PROXY_URL:
        return HTTPXRequest(proxy=PROXY_URL)
    return HTTPXRequest()
