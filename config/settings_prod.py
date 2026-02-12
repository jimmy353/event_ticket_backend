from .settings import *
from datetime import timedelta


DEBUG = False


ALLOWED_HOSTS = [
    "sirheartevents.com",
    "www.sirheartevents.com",
    "api.sirheartevents.com",
    "sirheartevents-onrender-com.onrender.com",
]


CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://sirheartevents.com",
    "https://www.sirheartevents.com",
    "https://api.sirheartevents.com",
    "https://sirheartevents-onrender-com.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://sirheartevents.com",
    "https://www.sirheartevents.com",
    "https://api.sirheartevents.com",
    "https://sirheartevents-onrender-com.onrender.com",
]


SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# Optional: Fix proxy issue on Render
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")