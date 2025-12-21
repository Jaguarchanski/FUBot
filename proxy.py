import os

def get_proxy():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASS")

    if not host:
        return None

    proxy_url = f"http://{user}:{password}@{host}:{port}"

    return {
        "http": proxy_url,
        "https": proxy_url
    }
