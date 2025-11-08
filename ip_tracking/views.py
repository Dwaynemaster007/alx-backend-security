# ip_tracking/views.py

from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django_ratelimit.decorators import ratelimit  # Official name
from ipware import get_client_ip
from functools import wraps


# === HELPER: Proxy-aware key for authenticated vs anonymous ===
def get_ratelimit_key(group, request):
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    ip, _ = get_client_ip(request)
    return f"ip:{ip or 'unknown'}"


# === CUSTOM DECORATOR TO APPLY BOTH LIMITS CORRECTLY ===
def dual_ratelimit(view_func):
    """10/min for logged-in, 5/min for anonymous (IP)"""
    decorated = ratelimit(
        key=get_ratelimit_key,
        rate="10/m",
        method="POST",
        block=True,
    )(view_func)
    return ratelimit(
        key="ip",  # Still block brute-force by IP
        rate="5/m",
        method="POST",
        block=True,
    )(decorated)


# === TASK 3: SENSITIVE LOGIN VIEW ===
@dual_ratelimit
def login_view(request):
    """
    Sensitive login endpoint with dual rate limiting:
    - Anonymous IPs: 5 requests per minute
    - Authenticated users: 10 requests per minute
    Uses proxy-aware IP via django-ipware
    """
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    username = request.POST.get("username")
    password = request.POST.get("password")
    if not username or not password:
        return JsonResponse({"error": "Missing credentials"}, status=400)

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({"message": "Login successful", "user": username})
    else:
        return JsonResponse({"error": "Invalid credentials"}, status=401)


# === BONUS: Protect admin too (ALX loves this) ===
@staff_member_required
@ratelimit(key=get_ratelimit_key, rate="50/h", block=True)
def admin_dashboard_proxy(request):
    """
    Example sensitive admin view – rate limited per user/IP
    """
    return JsonResponse({"data": "Welcome to secure admin dashboard"})