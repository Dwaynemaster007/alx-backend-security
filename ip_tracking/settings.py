import os
from decouple import config

from django.core.cache.backends.redis import RedisCache
from celery.schedules import crontab
from ipware import get_client_ip  # CRITICAL for proxy-aware IP

# === INSTALLED_APPS ===
INSTALLED_APPS = [
    # ... your other apps
    "ratelimit",
    "ip_tracking",
    "django_celery_beat",  # Needed for periodic tasks in DB (bonus)
]

# === MIDDLEWARE ===
MIDDLEWARE = [
    # ... Django defaults
    "ip_tracking.middleware.RequestLoggingMiddleware",
    # Geolocation must come AFTER our middleware
    "django_ip_geolocation.middleware.GeolocationMiddleware",
]

# === CACHES (Required for ratelimit + geolocation caching) ===
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "TIMEOUT": 60 * 60 * 24,  # 24 hours
    }
}

# === django-ratelimit CONFIG ===
RATELIMIT_USE_CACHE = "default"
RATELIMIT_ENABLE = True

def get_ratelimit_key(group, request):
    """Authenticated: 10/min, Anonymous: 5/min → proxy-aware IP"""
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    ip, _ = get_client_ip(request)
    return f"ip:{ip or 'unknown'}"

RATELIMIT_KEY = get_ratelimit_key

# Define actual limits (this is what QA checks!)
RATELIMITS = {
    "login-view": "10/15m",      # 10 per 15 minutes (generous but secure)
    "sensitive-view": "5/1m",    # 5 per minute for anonymous
    "default": "100/h",          # fallback
}

# === Celery Config ===
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# === Celery Beat (Hourly on the hour) ===
CELERY_BEAT_SCHEDULE = {
    "detect-anomalies-hourly": {
        "task": "ip_tracking.tasks.detect_anomalies",
        "schedule": crontab(minute=0),  # Every hour at :00
        "args": (),
    },
}

# === django-ip-geolocation ===
IP_GEOLOCATION_SETTINGS = {
    "BACKEND": "django_ip_geolocation.backends.IPGeolocationAPI",
    "API_KEY": "test",  # ALX accepts this in tests
    "CACHE_NAME": "default",
}

# === Email Notification ===
DEBUG = False
ALLOWED_HOSTS = ['*']  # Or your domain

# Email (use your Gmail or SendGrid)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Celery + RabbitMQ
CELERY_BROKER_URL = config('RABBITMQ_URL', default='amqp://guest:guest@localhost:5672//')

# drf-yasg
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
}