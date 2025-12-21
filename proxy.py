import os

def get_proxies():
    http = os.getenv("PROXY_HTTP")
    https = os.getenv("PROXY_HTTPS")

    if not http and not https:
        return None

    return {
        "http": http,
        "https": https
    }
