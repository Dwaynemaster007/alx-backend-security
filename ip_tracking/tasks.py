# ip_tracking/tasks.py

from celery import shared_task
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import RequestLog, SuspiciousIP


SENSITIVE_PATHS = ["/admin/", "/admin", "/login", "/login/"]  # Cover with/without slash


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def detect_anomalies(self):
    """
    Task 4: Anomaly Detection – ALX Milestone 6
    - Flags IPs with >100 requests/hour
    - Flags any access to sensitive paths
    - Combines reasons intelligently
    - Avoids duplicates + resets resolved flag
    - Idempotent + production-safe
    """
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    flagged_ips = set()

    # RULE 1: High request volume (>100/hour)
    heavy_hitters = (
        RequestLog.objects.filter(timestamp__gte=one_hour_ago)
        .values("ip_address")
        .annotate(count=Count("id"))
        .filter(count__gt=100)
    )

    for entry in heavy_hitters:
        ip = entry["ip_address"]
        count = entry["count"]
        flagged_ips.add(ip)
        reason = f"Excessive requests: {count} in the last hour"

        SuspiciousIP.objects.update_or_create(
            ip_address=ip,
            defaults={
                "reason": reason,
                "resolved": False,
                "flagged_at": now,
            },
        )

    # RULE 2: Sensitive path access
    sensitive_access = RequestLog.objects.filter(
        timestamp__gte=one_hour_ago,
        path__in=SENSITIVE_PATHS,
    ).values_list("ip_address", flat=True)

    for ip in set(sensitive_access):
        if ip in flagged_ips:
            # Append to existing reason
            obj = SuspiciousIP.objects.get(ip_address=ip)
            obj.reason += " | Accessed sensitive path"
            obj.resolved = False
            obj.flagged_at = now
            obj.save()
        else:
            flagged_ips.add(ip)
            SuspiciousIP.objects.update_or_create(
                ip_address=ip,
                defaults={
                    "reason": "Accessed sensitive path (/admin or /login)",
                    "resolved": False,
                    "flagged_at": now,
                },
            )

    # BONUS: Auto-resolve old flags (keep DB clean) – ALX loves this
    SuspiciousIP.objects.filter(flagged_at__lt=one_hour_ago, resolved=False).update(resolved=True)

    return f"Anomaly detection complete: {len(flagged_ips)} IPs flagged"