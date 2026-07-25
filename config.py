import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(".env"))

DATABASE_URL = os.getenv("DBURL")
if not DATABASE_URL:
    raise RuntimeError("DBURL environment variable not set")

SECRET = os.getenv("SECRET")
if not SECRET:
    raise RuntimeError("SECRET environment variable not set")

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7