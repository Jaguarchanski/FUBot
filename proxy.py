import os

# Очікує наступні змінні в Render Environment
# PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, PROXY_COUNTRY
# Наприклад:
# PROXY_HOST=123.45.67.89
# PROXY_PORT=8080
# PROXY_USER=myuser
# PROXY_PASS=mypass

def get_proxy_dict():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASS")
    
    if not host or not port:
        return None  # без проксі

    proxy_url = f"http://{user}:{password}@{host}:{port}" if user and password else f"http://{host}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }
