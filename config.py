import os
from dotenv import load_dotenv

load_dotenv()


def _get_config_val(name, default=None):
    """
    ดึงค่า Configuration ตามลำดับความสำคัญ:
    1. Streamlit Secrets (st.secrets)
       - รูปแบบ [connections.mysql] ตามคู่มือทางการของ Streamlit
       - รูปแบบ Flat keys เช่น st.secrets["DB_HOST"]
    2. Environment variables (.env หรือ OS environment)
    3. ค่า Default
    """
    # 1. พยายามอ่านจาก Streamlit Secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            # 1.1 ตรวจสอบรูปแบบ [connections.mysql]
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

            # 1.2 ตรวจสอบรูปแบบ Flat keys
            if name in st.secrets:
                return st.secrets[name]
    except Exception:
        pass

    # 2. พยายามอ่านจาก Environment Variables (.env หรือ OS)
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


# พอร์ตฐานข้อมูล (TiDB Cloud ใช้พอร์ต 4000, MySQL ทั่วไปใช้ 3306)
DB_PORT = int(_get_config_val("DB_PORT", 3306))

# คอนฟิกการเชื่อมต่อ MySQL / TiDB
DB_CONFIG = {
    'host': _require('DB_HOST'),
    'user': _require('DB_USER'),
    'password': _get_config_val('DB_PASSWORD', ''),
    'database': _require('DB_NAME'),
    'port': DB_PORT,
}

# จัดการ SSL / TLS สำหรับ Cloud Database (โดยเฉพาะ TiDB Cloud Serverless)
ssl_disabled = _get_config_val("DB_SSL_DISABLED")
if ssl_disabled is not None:
    if isinstance(ssl_disabled, str):
        DB_CONFIG["ssl_disabled"] = ssl_disabled.lower() in ("true", "1", "yes")
    else:
        DB_CONFIG["ssl_disabled"] = bool(ssl_disabled)
else:
    # หากไม่ได้ปิด SSL และเชื่อมต่อ Remote Host (เช่น TiDB Cloud)
    db_host = DB_CONFIG["host"].lower()
    if db_host not in ("localhost", "127.0.0.1") and ("tidb" in db_host or DB_PORT == 4000):
        ssl_ca = _get_config_val("DB_SSL_CA")
        if not ssl_ca:
            # ใช้ CA Bundle จาก certifi หรือระบบ Linux
            if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
                ssl_ca = "/etc/ssl/certs/ca-certificates.crt"
            else:
                try:
                    import certifi
                    ssl_ca = certifi.where()
                except ImportError:
                    pass

        if ssl_ca:
            DB_CONFIG["ssl_ca"] = ssl_ca
            DB_CONFIG["ssl_verify_cert"] = True

# RID API URL
RID_API_URL = _get_config_val('RID_API_URL', 'https://app.rid.go.th/reservoir/api/dam/public/')
