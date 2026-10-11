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
EMAIL_VERIFICATION_REQUIRED = os.getenv("EMAIL_VERIFICATION_REQUIRED", "false").lower() == "true"
PASSWORD_RECOVERY_ENABLED = os.getenv("PASSWORD_RECOVERY_ENABLED", "false").lower() == "true"
# Only local automated tests may expose mail links; never enable on a public demo.
EXPOSE_DEMO_MAIL = os.getenv("EXPOSE_DEMO_MAIL", "false").lower() == "true"
TRUST_CLOUDFLARE = os.getenv("TRUST_CLOUDFLARE", "false").lower() == "true"
# disabled / local / external. External configuration alone is not proof of official FSP access.
FSP_MODE = os.getenv("FSP_MODE", "disabled")
FSP_ISSUER = os.getenv("FSP_ISSUER", "").rstrip("/")
FSP_BACKCHANNEL_ORIGIN = os.getenv("FSP_BACKCHANNEL_ORIGIN", "").rstrip("/")
FSP_CLIENT_ID = os.getenv("FSP_CLIENT_ID", "razryad")
FSP_CLIENT_SECRET = os.getenv("FSP_CLIENT_SECRET", "")
FSP_FLOW_SECRET = os.getenv("FSP_FLOW_SECRET", "")
FSP_ACHIEVEMENTS_URL = os.getenv("FSP_ACHIEVEMENTS_URL", "")
