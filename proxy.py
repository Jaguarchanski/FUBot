import os

def get_proxy():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASS")

    if not host or not port:
        return None

    if user and password:
        return f"http://{user}:{password}@{host}:{port}"
    return f"http://{host}:{port}"
