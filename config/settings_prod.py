from .settings import *
from datetime import timedelta

DEBUG = False

ALLOWED_HOSTS = [
    "yourdomain.com",
    "api.yourdomain.com",
]

CORS_ALLOW_ALL_ORIGINS = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}
