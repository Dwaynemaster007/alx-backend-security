MIDDLEWARE = [
    # Django default middleware…
    "ip_tracking.middleware.RequestLoggingMiddleware",
]
INSTALLED_APPS = [
    # Django apps...
    "ratelimit",
    "ip_tracking",
]
def user_or_ip(request):
    """Use username for logged-in users, otherwise fallback to IP."""
    if request.user.is_authenticated:
        return str(request.user.pk)
    return request.META.get("REMOTE_ADDR")


RATELIMIT_KEY = "user_or_ip"
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_BEAT_SCHEDULE = {
    "detect-anomalies-hourly": {
        "task": "ip_tracking.tasks.detect_anomalies",
        "schedule": 3600.0,  # every hour
    },
}