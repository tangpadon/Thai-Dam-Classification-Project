import os
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()


def _get_config_val(name, default=None):
    # พยายามอ่านจาก Streamlit Secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            # ตรวจสอบรูปแบบ [connections.mysql]
            if "connections" in st.secrets and "mysql" in st.secrets["connections"]:
                mysql_sec = st.secrets["connections"]["mysql"]
                mapping = {
                    "DB_HOST": "host",
                    "DB_PORT": "port",
                    "DB_USER": "username",
                    "DB_PASSWORD": "password",
                    "DB_NAME": "database",
                }
                if name in mapping and mapping[name] in mysql_sec:
                    return mysql_sec[mapping[name]]
                if name == "DB_USER" and "user" in mysql_sec:
                    return mysql_sec["user"]

            # ตรวจสอบรูปแบบ Flat keys
            if name in st.secrets:
                return st.secrets[name]
    except Exception:
        pass

    # พยายามอ่านจาก Environment Variables
    val = os.getenv(name)
    if val is not None and val != "":
        return val

    return default


def _require(name):
    val = _get_config_val(name)
    if val is None:
        raise RuntimeError(
            f"Missing required configuration: '{name}'. "
            "กรุณาระบุใน .streamlit/secrets.toml (บน Streamlit Community Cloud) หรือในไฟล์ .env (เครื่อง Local)"
        )
    return val


# พอร์ตฐานข้อมูล MySQL (ค่าเริ่มต้น 3306)
DB_PORT = int(_get_config_val("DB_PORT", 3306))

# คอนฟิกการเชื่อมต่อ MySQL
DB_CONFIG = {
    'host': _require('DB_HOST'),
    'user': _require('DB_USER'),
    'password': _get_config_val('DB_PASSWORD', ''),
    'database': _require('DB_NAME'),
    'port': DB_PORT,
}

# RID API URL
RID_API_URL = _get_config_val('RID_API_URL', 'https://app.rid.go.th/reservoir/api/dam/public/')
