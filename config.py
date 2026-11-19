import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "skillbridge_jp")

    # Fernet key (generate once: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    FERNET_KEY = os.getenv("FERNET_KEY")
    if not FERNET_KEY:
        raise RuntimeError("FERNET_KEY missing. Put it in .env")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads/resumes")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB