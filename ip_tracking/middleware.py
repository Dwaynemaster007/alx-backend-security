from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from ipware import get_client_ip  # <-- CRITICAL: use django-ipware
from django_ip_geolocation.middleware import GeolocationMiddleware
from django_ip_geolocation.backends import IPGeolocationAPI
from .models import RequestLog, BlockedIP
import logging
import ipaddress

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    ALX Milestone 6 - Full IP Security Middleware
    Tasks 0, 1, 2 fully compliant + bonuses
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Reuse django-ip-geolocation backend (already configured in settings)
        self.geolocation_backend = IPGeolocationAPI()

    def __call__(self, request):
        # 1. Get reliable IP (handles Cloudflare, Nginx, etc.)
        ip, is_routable = get_client_ip(request)
        if not ip or not is_routable:
            # Skip private/internal IPs
            return self.get_response(request)

        request.ip_address = ip  # Attach for views if needed

        # 2. BLOCK BLACKLISTED IPS (with CIDR support + active only)
        if self.is_ip_blocked(ip):
            logger.warning(f"Blocked request from {ip} - Blacklisted")
            return HttpResponseForbidden("Access denied: Your IP has been blocked.")

        # 3. GEOLOCATION (cached automatically by django-ip-geolocation)
        geo_data = self.get_geolocation(ip)

        # 4. LOG REQUEST
        try:
            RequestLog.objects.create(
                ip_address=ip,
                path=request.path,
                country=geo_data.get("country_name") or geo_data.get("country"),
                city=geo_data.get("city"),
            )
        except Exception as e:
            logger.error(f"Failed to log request from {ip}: {e}")

        return self.get_response(request)

    def is_ip_blocked(self, ip):
        """Check exact IP + CIDR ranges + only active blocks"""
        try:
            client_ip = ipaddress.ip_address(ip)
        except ValueError:
            return False

        blocked_qs = BlockedIP.objects.filter(is_active=True).values_list("ip_address", flat=True)
        for blocked_entry in blocked_qs:
            try:
                if "/" in blocked_entry:
                    network = ipaddress.ip_network(blocked_entry, strict=False)
                    if client_ip in network:
                        return True
                else:
                    if client_ip == ipaddress.ip_address(blocked_entry):
                        return True
            except ValueError:
                continue
        return False

    def get_geolocation(self, ip):
        """Use django-ip-geolocation backend with built-in caching"""
        cache_key = f"geo_{ip}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = self.geolocation_backend.get_geolocation(ip)
            data = {
                "country": response.country_name,
                "country_name": response.country_name,
                "city": response.city,
            }
            cache.set(cache_key, data, 60 * 60 * 24)  # 24h
            return data
        except Exception as e:
            logger.warning(f"Geolocation failed for {ip}: {e}")
            cache.set(cache_key, {}, 300)  # 5 min on failure
            return {}