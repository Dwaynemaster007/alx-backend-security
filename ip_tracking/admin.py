from django.contrib import admin

from .models import BlockedIP, RequestLog, SuspiciousIP

admin.site.register(RequestLog)
admin.site.register(BlockedIP)
admin.site.register(SuspiciousIP)
