from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from ratelimit.decorators import ratelimit


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@ratelimit(key="user_or_ip", rate="10/m", method="POST", block=True)
def login_view(request):
    """
    Login view protected by IP-based and user-based rate limiting.
    - Anonymous: 5 requests/min
    - Authenticated: 10 requests/min
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({"message": "Login successful"})
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    return JsonResponse({"detail": "Send a POST request with username and password."})
