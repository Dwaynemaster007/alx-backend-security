from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone


class RequestLog(models.Model):
    """
    Logs every incoming request with IP, path, and geolocation.
    Optimized for high-traffic with indexing.
    """
    ip_address = models.GenericIPAddressField(
        protocol="both",
        unpack_ipv4=True,
        db_index=True,
        help_text="Client IP address (anonymized in production)",
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

    def save(self, *args, **kwargs):
        """
        Optional: Anonymize IP in production (GDPR)
        e.g., 192.168.1.100 → 192.168.1.0
        """
        if not settings.DEBUG:
            import ipaddress
            try:
                ip = ipaddress.ip_address(self.ip_address)
                if ip.version == 4:
                    self.ip_address = str(ipaddress.IPv4Network(f"{self.ip_address}/24", strict=False)[0])
                elif ip.version == 6:
                    self.ip_address = str(ipaddress.IPv6Network(f"{self.ip_address}/64", strict=False)[0])
            except Exception:
                pass  # Keep original if invalid
        super().save(*args, **kwargs)


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