import os
from config import PROXY_URL

def get_proxy():
    if PROXY_URL:
        return PROXY_URL
    return None
