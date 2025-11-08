# ip_tracking/management/commands/block_ip.py

from django.core.management.base import BaseCommand
from ip_tracking.models import BlockedIP
import ipaddress


class Command(BaseCommand):
    help = "Block an IP address or CIDR range with optional reason."

    def add_arguments(self, parser):
        parser.add_argument("ip", type=str, help="IP address or CIDR range (e.g. 192.168.1.100 or 192.168.1.0/24)")
        parser.add_argument(
            "--reason",
            type=str,
            default="Manually blocked via command",
            help="Reason for blocking (visible in admin)",
        )

    def handle(self, *args, **options):
        ip_input = options["ip"]
        reason = options["reason"]

        # Validate IP or CIDR
        try:
            network = ipaddress.ip_network(ip_input, strict=False)
            ip_str = str(network)  # Normalizes to CIDR form
        except ValueError:
            self.stderr.write(self.style.ERROR(f"Invalid IP or CIDR: {ip_input}"))
            return

        # Block it
        blocked, created = BlockedIP.objects.update_or_create(
            ip_address=ip_str,
            defaults={"reason": reason, "is_active": True},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully blocked: {ip_str} → {reason}")
            )
        else:
            # Update reason even if already exists
            if blocked.reason != reason:
                blocked.reason = reason
                blocked.save()
            self.stdout.write(
                self.style.WARNING(f"Already blocked: {ip_str} (reason updated)")
            )