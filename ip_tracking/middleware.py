from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.core.cache.backends.base import InvalidCacheBackendError
from ipgeolocation import IpGeoLocation
from .models import RequestLog, BlockedIP
import logging

# Configure logger
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Comprehensive IP Security Middleware:
    - Blocks blacklisted IPs
    - Logs request with IP, path, timestamp, and geolocation
    - Caches geolocation results for 24 hours
    - Handles proxies and errors gracefully
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Initialize only if API key is configured
        self.geo = None
        try:
            self.geo = IpGeoLocation()
        except Exception as e:
            logger.warning(f"IP Geolocation disabled: {e}")

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        if not ip_address:
            return self.get_response(request)  # Skip if no IP

        # 1. BLOCK BLACKLISTED IPS
        if BlockedIP.objects.filter(ip_address=ip_address).exists():
            logger.warning(f"Blocked request from blacklisted IP: {ip_address}")
            return HttpResponseForbidden("Access denied: Your IP is blocked.")

        # 2. GEOLOCATION (cached)
        geo_data = self.get_geolocation(ip_address)

        # 3. LOG REQUEST
        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                timestamp=timezone.now(),
                path=request.path,
                country=geo_data.get("country"),
                city=geo_data.get("city"),
            )
        except Exception as e:
            logger.error(f"Failed to log request from {ip_address}: {e}")

        return self.get_response(request)

    def get_client_ip(self, request):
        """
        Reliably extract client IP, handling proxies.
        Uses HTTP_X_FORWARDED_FOR with fallback to REMOTE_ADDR.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Take first IP (closest to client)
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        # Basic validation
        return ip if ip and self.is_valid_ip(ip) else None

    def is_valid_ip(self, ip):
        """Basic IP format validation"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def get_geolocation(self, ip_address):
        """
        Fetch and cache geolocation data.
        Returns {'country': ..., 'city': ...}
        """
        cache_key = f"geo:{ip_address}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        if not self.geo:
            return {"country": None, "city": None}

        try:
            geo_info = self.geo.lookup(ip_address)
            geo_data = {
                "country": geo_info.get("country_name") or None,
                "city": geo_info.get("city") or None,
            }
            cache.set(cache_key, geo_data, timeout=60 * 60 * 24)  # 24 hours
            return geo_data
        except Exception as e:
            logger.warning(f"Geolocation failed for {ip_address}: {e}")
            # Cache failure to avoid repeated API calls
            cache.set(cache_key, {"country": None, "city": None}, timeout=60 * 5)  # 5 min
            return {"country": None, "city": None}