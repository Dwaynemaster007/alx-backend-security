from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.cache import cache
from ipgeolocation import IpGeoLocation
from .models import RequestLog, BlockedIP


class RequestLoggingMiddleware:
    """
    Middleware to:
    - Block requests from blacklisted IPs
    - Log all requests (IP, timestamp, path, geolocation)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.geo = IpGeoLocation()  # django-ipgeolocation client

    def __call__(self, request):
        ip_address = self.get_client_ip(request)

        # Block if IP is in blacklist
        if BlockedIP.objects.filter(ip_address=ip_address).exists():
            return HttpResponseForbidden("Your IP has been blocked.")

        # Get cached geolocation (24h cache)
        cache_key = f"geo:{ip_address}"
        geo_data = cache.get(cache_key)

        if not geo_data:
            try:
                geo_info = self.geo.lookup(ip_address)
                geo_data = {
                    "country": geo_info.get("country_name"),
                    "city": geo_info.get("city"),
                }
                cache.set(cache_key, geo_data, timeout=60 * 60 * 24)  # 24 hours
            except Exception:
                geo_data = {"country": None, "city": None}

        # Log request
        RequestLog.objects.create(
            ip_address=ip_address,
            timestamp=timezone.now(),
            path=request.path,
            country=geo_data.get("country"),
            city=geo_data.get("city"),
        )

        return self.get_response(request)

    def get_client_ip(self, request):
        """
        Extract client IP address from request headers.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
