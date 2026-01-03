import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FUNDING_THRESHOLD_FREE = 1.5  # % для безкоштовного плану
