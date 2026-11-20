from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import BlockedIP, RequestLog, SuspiciousIP
from .tasks import detect_anomalies

PUBLIC_IP = '8.8.8.8'


@mock.patch('ip_tracking.middleware.IPGeolocationAPI')
class MiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()

    def get(self, path='/sensitive/', ip=PUBLIC_IP):
        return self.client.get(path, REMOTE_ADDR=ip)

    def test_logs_request_with_location(self, geo):
        geo.return_value.data.return_value = {'county': {'name': 'United States'}, 'raw_data': {'city': 'Mountain View'}}
        self.get()
        log = RequestLog.objects.get()
        self.assertEqual((log.ip_address, log.path, log.country, log.city), (PUBLIC_IP, '/sensitive/', 'United States', 'Mountain View'))

    def test_private_ips_are_not_logged(self, geo):
        self.get(ip='127.0.0.1')
        self.assertFalse(RequestLog.objects.exists())

    def test_blocked_ip_and_range(self, geo):
        BlockedIP.objects.create(ip_address=PUBLIC_IP)
        self.assertEqual(self.get().status_code, 403)
        BlockedIP.objects.create(ip_address='1.1.0.0/16')
        self.assertEqual(self.get(ip='1.1.1.1').status_code, 403)
        self.assertNotEqual(self.get(ip='9.9.9.9').status_code, 403)

    def test_inactive_block_is_ignored(self, geo):
        BlockedIP.objects.create(ip_address=PUBLIC_IP, is_active=False)
        self.assertNotEqual(self.get().status_code, 403)

    def test_geolocation_failure_still_logs(self, geo):
        geo.side_effect = RuntimeError('API down')
        self.get()
        self.assertIsNone(RequestLog.objects.get().country)


class BlockIpCommandTests(TestCase):
    def run_command(self, *args):
        out, err = StringIO(), StringIO()
        call_command('block_ip', *args, stdout=out, stderr=err)
        return out.getvalue() + err.getvalue()

    def test_blocks_ip_range_and_ipv6(self):
        self.run_command('203.0.113.7', '--reason', 'spam')
        self.run_command('198.51.100.0/24')
        self.run_command('2001:db8::/32')
        self.assertEqual(
            sorted(BlockedIP.objects.values_list('ip_address', flat=True)),
            ['198.51.100.0/24', '2001:db8::/32', '203.0.113.7'],
        )

    def test_rejects_invalid_input(self):
        self.assertIn('Invalid', self.run_command('not-an-ip'))
        self.assertFalse(BlockedIP.objects.exists())


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_sensitive_view_limit(self):
        codes = [self.client.get('/sensitive/').status_code for _ in range(6)]
        self.assertEqual(codes[:5], [200] * 5)
        self.assertIn(codes[5], (403, 429))

    def test_login_requires_post_and_credentials(self):
        self.assertEqual(self.client.get('/login/').status_code, 405)
        self.assertEqual(self.client.post('/login/', {'username': 'x'}).status_code, 400)
        self.assertEqual(self.client.post('/login/', {'username': 'x', 'password': 'y'}).status_code, 401)


class AnomalyDetectionTests(TestCase):
    def test_flags_heavy_and_sensitive_traffic(self):
        now = timezone.now()
        RequestLog.objects.bulk_create([RequestLog(ip_address='203.0.113.1', path='/', timestamp=now) for _ in range(101)])
        RequestLog.objects.create(ip_address='203.0.113.2', path='/admin/', timestamp=now)
        RequestLog.objects.create(ip_address='203.0.113.3', path='/admin/', timestamp=now - timedelta(hours=2))
        detect_anomalies.apply()
        flagged = dict(SuspiciousIP.objects.values_list('ip_address', 'reason'))
        self.assertIn('Excessive requests: 101', flagged['203.0.113.1'])
        self.assertIn('sensitive path', flagged['203.0.113.2'])
        self.assertNotIn('203.0.113.3', flagged)
