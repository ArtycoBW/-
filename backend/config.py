"""Настройки окружения. Демо-функции включаются только явно."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./.local/razryad.db")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "http://localhost:3000")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_FROM = os.getenv("SMTP_FROM", "hello@razryad.local")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "false").lower() == "true"
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_DIR = os.getenv("MAIL_DIR", ".local/mail")
MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.json")
