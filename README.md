
# Django IP Security & Analytics  
**ALX ProDev Backend — Milestone 6**

A **production-grade IP tracking system** built with Django that logs, blacklists, geolocates, rate-limits, and detects anomalies — all while staying **GDPR-compliant** and **scalable**.

[![Django](https://img.shields.io/badge/Django-5.0-306998?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-000?style=for-the-badge&logo=vercel)](https://vercel.com)

---

## Features

| Feature | Implementation |
|-------|----------------|
| **IP Logging** | Middleware logs `ip`, `path`, `timestamp` |
| **IP Blacklisting** | `BlockedIP` model + 403 response |
| **Geolocation** | `django-ipgeolocation` + 24h Redis cache |
| **Rate Limiting** | `django-ratelimit` (10/min auth, 5/min anon) |
| **Anomaly Detection** | Celery task flags >100 req/hour |
| **Privacy** | Anonymized IPs, auto-delete logs |

---

## Project Structure

```
alx-backend-security/
├── ip_tracking/
│   ├── middleware.py          # Logs + blocks + geolocates
│   ├── models.py              # RequestLog, BlockedIP, SuspiciousIP
│   ├── views.py               # Rate-limited login view
│   ├── tasks.py               # Celery anomaly detection
│   └── management/
│       └── commands/
│           └── block_ip.py    # CLI to block IPs
├── settings.py               # Middleware, ratelimit, Redis config
├── celery_config.py           # Celery + Redis broker
└── requirements.txt
```

---

## Tech Stack

- **Django 5.0** — Core framework
- **django-ipware** — Accurate IP extraction behind proxies
- **django-ipgeolocation** — Country/city lookup
- **django-ratelimit** — Rate limiting
- **Redis** — Caching + rate limit backend
- **Celery** — Async anomaly detection
- **PostgreSQL** — Production DB (SQLite for dev)

---

## Setup & Installation

```bash
# 1. Clone the repo
git clone https://github.com/Dwaynemaster007/alx-backend-security.git
cd alx-backend-security

# 2. Create virtual env
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Start Redis (in another terminal)
redis-server

# 6. Run Celery worker
celery -A alx_backend_security worker -l info

# 7. Start Django
python manage.py runserver
```

---

## Environment Variables (`.env`)

```env
IPGEOLOCATION_API_KEY=your_ipinfo_token
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
```

---

## Usage

### Block an IP
```bash
python manage.py block_ip 203.0.113.55
```

### View Logs
```sql
SELECT * FROM ip_tracking_requestlog ORDER BY timestamp DESC LIMIT 10;
```

### Trigger Anomaly Detection
```bash
celery -A alx_backend_security call ip_tracking.tasks.detect_anomalies
```

---

## API Endpoints (Protected)

| Endpoint | Rate Limit |
|--------|------------|
| `POST /api/login/` | 5/min (anon), 10/min (auth) |
| `GET /admin/` | Blocked if IP in blacklist |

---

## Privacy & Compliance

- IPs anonymized after 30 days
- GDPR/CCPA-compliant data retention
- No PII stored
- Transparent privacy policy required

---

## Testing

```bash
python manage.py test ip_tracking
```

---

## Deployment (Production)

1. Use **PostgreSQL** + **Redis**
2. Set `DEBUG=False`
3. Deploy with **Gunicorn + Nginx**
4. Use **Celery Beat** for scheduled tasks

---

## Author

**Thubelihle Dlamini**  
[@Dwaynemaster007](https://github.com/Dwaynemaster007)  
ALX ProDev Backend — Milestone 6

---

<div align="center">

### Built with security, scale, and ethics in mind

[![GitHub](https://img.shields.io/badge/GitHub-Dwaynemaster007-181717?style=for-the-badge&logo=github)](https://github.com/Dwaynemaster007)

**Tags:** `django` `security` `ip-tracking` `geolocation` `rate-limiting` `celery` `redis` `gdpr` `alx-backend`

</div>