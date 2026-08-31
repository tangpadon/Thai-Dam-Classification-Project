import os
from dotenv import load_dotenv

load_dotenv()


def _require(name):
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name} (ดูไฟล์ .env.example)")
    return value


DB_CONFIG = {
    'host': _require('DB_HOST'),
    'user': _require('DB_USER'),
    'password': _require('DB_PASSWORD'),
    'database': _require('DB_NAME'),
}

RID_API_URL = _require('RID_API_URL')
