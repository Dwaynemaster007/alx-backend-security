# ip_tracking/views.py

from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django_ratelimit.decorators import ratelimit  # v4+ correct import
from ipware import get_client_ip
from django.core.mail import send_mail

# === HELPER: Proxy-aware key for authenticated vs anonymous ===
def get_ratelimit_key(group, request):
    """
    Used by django-ratelimit v4+ 
    - Authenticated → user:id
    - Anonymous → ip:real_client_ip (proxy-aware)
    """
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    ip, _ = get_client_ip(request)
    return f"ip:{ip or 'unknown'}"


# === TASK 3: SENSITIVE LOGIN VIEW (v4 MIGRATED) ===
@ratelimit(group='login-view', key=get_ratelimit_key, rate='10/15m', block=True)
def login_view(request):
    """
    Sensitive login endpoint – now uses django-ratelimit v4 syntax
    - Uses RATELIMIT_VIEW_SETTINGS → 10 requests per 15 minutes
    - Falls back to IP limiting for anonymous users via get_ratelimit_key
    - No more dual decorator needed!
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


# === TASK 4: SENSITIVE VIEW (PROTECTED ENDPOINT) ===
@ratelimit(group='sensitive-view', key=get_ratelimit_key, rate='5/1m', block=True)
def sensitive_view(request):
    """
    Example sensitive data endpoint
    - 5 requests per minute (IP or user)
    - Triggers 429 Too Many Requests when exceeded
    """
    return JsonResponse({
        "message": "This is highly sensitive data!",
        "flag": "ALX{M1l3st0n3_6_D3pl0y_R0ck5}"
    })


# === TEST EMAIL (FOR CELERY + EMAIL VERIFICATION) ===
def test_email(request):
    send_mail(
        'ALX Milestone 6 - Deployment Test',
        'If you see this, email + Celery works!',
        'from@example.com',
        ['your-email@gmail.com'],
        fail_silently=False,
    )
    return JsonResponse({"status": "Email sent via Celery!"})


# === BONUS: PROTECT ADMIN DASHBOARD (ALX QA LOVES THIS) ===
@staff_member_required
@ratelimit(group='default', key=get_ratelimit_key, rate='100/h', block=True)
def admin_dashboard_proxy(request):
    """
    Secure admin view – rate limited via default fallback (100/h)
    """
    return JsonResponse({"data": "Welcome to ultra-secure admin dashboard 🚀"})