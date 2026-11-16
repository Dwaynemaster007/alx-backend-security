from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('sensitive/', views.sensitive_view, name='sensitive'),
    path('test-email/', views.test_email, name='test-email'),
    path('admin-dashboard/', views.admin_dashboard_proxy, name='admin-dashboard'),
]
