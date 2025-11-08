from django.db import models
from django.utils import timezone
from django.conf import settings  # Required for DEBUG check in anonymized_ip()


class RequestLog(models.Model):
    """
    Logs every incoming request with IP, path, and geolocation.
    Optimized for high-traffic with indexing.
    """
    ip_address = models.GenericIPAddressField(
        protocol="both",
        unpack_ipv4=True,
        db_index=True,
        help_text="Client IP address (stored raw for accurate blocking)",
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the request was received",
    )
    path = models.CharField(
        max_length=2048,
        db_index=True,
        help_text="Requested URL path",
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country from geolocation",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City from geolocation",
    )

    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["ip_address", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.ip_address} → {self.path} [{self.timestamp.strftime('%Y-%m-%d %H:%M')}]"

    def anonymized_ip(self):
        """Return GDPR/CCPA-compliant IP for reports and admin display"""
        if settings.DEBUG:
            return self.ip_address
        try:
            import ipaddress
            ip = ipaddress.ip_address(self.ip_address)
            if ip.version == 4:
                parts = self.ip_address.split('.')
                return '.'.join(parts[:3]) + '.0'
            else:  # IPv6
                return ':'.join(self.ip_address.split(':')[:4]) + '::'
        except Exception:
            return "unknown"


class BlockedIP(models.Model):
    """
    Blacklisted IP addresses — instant 403 response.
    """
    ip_address = models.GenericIPAddressField(
        unique=True,
        protocol="both",
        db_index=True,
        help_text="Blocked IP address or CIDR range",
    )
    blocked_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this IP was blocked",
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Why this IP was blocked",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to temporarily unblock",
    )

    class Meta:
        verbose_name = "Blocked IP"
        verbose_name_plural = "Blocked IPs"
        ordering = ["-blocked_at"]

    def __str__(self):
        return f"Blocked: {self.ip_address} ({'Active' if self.is_active else 'Inactive'})"


class SuspiciousIP(models.Model):
    """
    IPs flagged by anomaly detection.
    """
    ip_address = models.GenericIPAddressField(
        db_index=True,
        help_text="Suspicious IP address",
    )
    reason = models.TextField(
        help_text="Why this IP was flagged (e.g., 150 req/hour)",
    )
    flagged_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When anomaly was detected",
    )
    resolved = models.BooleanField(
        default=False,
        help_text="Mark as resolved after review",
    )

    class Meta:
        verbose_name = "Suspicious IP"
        verbose_name_plural = "Suspicious IPs"
        ordering = ["-flagged_at"]
        indexes = [
            models.Index(fields=["ip_address", "flagged_at"]),
        ]

    def __str__(self):
        status = "Resolved" if self.resolved else "Active"
        return f"Suspicious: {self.ip_address} [{status}]"