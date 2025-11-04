from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import Count
from .models import RequestLog, SuspiciousIP


SENSITIVE_PATHS = ["/admin", "/login"]


@shared_task
def detect_anomalies():
    """
    Detect suspicious IPs:
    - More than 100 requests in the past hour
    - Accessing sensitive paths (/admin, /login)
    """

    one_hour_ago = timezone.now() - timedelta(hours=1)

    # Rule 1: IPs exceeding 100 requests/hour
    heavy_users = (
        RequestLog.objects.filter(timestamp__gte=one_hour_ago)
        .values("ip_address")
        .annotate(request_count=Count("id"))
        .filter(request_count__gt=100)
    )

    for entry in heavy_users:
        ip = entry["ip_address"]
        SuspiciousIP.objects.get_or_create(
            ip_address=ip,
            reason="Exceeded 100 requests in the past hour",
        )

    # Rule 2: Accessing sensitive paths
    sensitive_hits = RequestLog.objects.filter(
        timestamp__gte=one_hour_ago, path__in=SENSITIVE_PATHS
    ).values_list("ip_address", flat=True)

    for ip in set(sensitive_hits):
        SuspiciousIP.objects.get_or_create(
            ip_address=ip,
            reason="Accessed sensitive path (/admin or /login)",
        )
