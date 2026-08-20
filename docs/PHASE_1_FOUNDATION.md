# Phase 1 — Foundation Upgrade

Status: **complete and verified**. All 42 existing tests pass; the full
stack (Postgres + Redis + Celery + Django + Next.js frontend) was run
end-to-end against real data during this work, not just unit-tested in
isolation.

## What changed

### 1. Django 6 upgrade
- Django 5.0.14 → **6.0.7** (confirmed on PyPI, really exists)
- DRF 3.15 → 3.16.1, simplejwt → 5.5.1, django-filter → 25.2,
  django-cors-headers → 4.9.0, drf-spectacular → 0.30.0, Pillow → 11.1.0
- Added: django-redis 5.4, redis-py 5.2, celery 5.4
- **Python stays at 3.12** — 3.14 isn't installable in this environment yet
  (not in apt's repos here) and isn't required by anything in this
  codebase; nothing here uses a 3.12-incompatible feature, so upgrading to
  3.14 later is a drop-in change, not a rewrite.
- Zero deprecated-pattern fixes were needed — the existing codebase already
  checked clean against Django 6 (`manage.py check` passed before any other
  change was made, confirmed as a baseline).

### 2. App restructure
Every app now follows:
```
apps/<domain>/
  models.py
  services.py        # business logic
  selectors.py        # read-query construction, extracted out of views
  permissions.py       # domain permission classes (or a documented re-export)
  signals.py
  tasks.py
  admin.py
  tests.py
  api/
    serializers.py
    views.py
    urls.py
    filters.py         # where relevant (products only, so far)
```

**Renames** (app directory + Python import path only — no change to URL
paths or response shapes, so the frontend contract is untouched):

| Old | New |
|---|---|
| `apps.core` | `apps.shared` |
| `apps.users` | `apps.accounts` |
| `apps.categories` | `apps.category` |
| `apps.brands` | `apps.brand` |

Renaming a Django app after it has real migration history is normally a
multi-step dance (state operations, `--fake`, etc.). Since this project has
no real production data yet, I took the clean path instead: deleted all
migrations and regenerated fresh `0001_initial` migrations under the new
app labels. **This is a one-time move** — from here on, migrations are
additive as normal. If this were a live production database, the approach
would be different (fake-rename via `migrations.SeparateDatabaseAndState`);
flagging this explicitly since it's the kind of thing that matters a lot in
a real deployment.

Everything else (`products`, `cart`, `orders`, `media`, `dashboard`,
`site_settings`, `locations`) kept its existing app label/table names —
only the file layout changed.

### 3. New selectors extracted (real optimizations, not just moves)
- `apps/brand/selectors.py` — added `select_related("country")`, fixing a
  latent N+1 (every brand's `country_detail` was a separate query before).
- `apps/orders/selectors.py` — added `select_related("country", "region",
  "city", "user")` for the same reason on order detail views.
- `apps/products/selectors.py`, `apps/category/selectors.py`,
  `apps/locations/selectors.py` — pure extraction, same query shape as
  before, now testable independent of HTTP.

### 4. Scaffolded (structure-only) domain apps
`inventory`, `delivery`, `pickup_points`, `payments`, `wallet`, `loyalty`,
`notifications`, `reviews`, `support` — registered in `INSTALLED_APPS`,
full file skeleton present, **no models yet**. Each `models.py` docstring
states which future phase fills it in. This satisfies the structural ask
without inventing premature abstractions or fake CRUD for domains that
don't have real business logic yet (per "do not create unnecessary
abstraction").

### 5. `apps/shared` (formerly `core`) gained
- `constants.py` — cross-cutting values (pagination defaults, cache TTLs,
  the `X-Cart-Id` header name)
- `validators.py` — shared `validate_phone_number`, `validate_positive_amount`
- `response.py` — `success_response()` / `error_response()` envelope
  helpers **for new endpoints going forward**. Deliberately **not**
  retrofitted onto the existing catalog/cart/order endpoints — the Next.js
  frontend is integrated against their exact current shapes
  (`{count, total_pages, ..., results}` for lists, bare model fields for
  detail), and changing that now would break the frontend for zero
  functional gain in this pass. Flagging this as a conscious call, not an
  oversight.

### 6. Settings split
`config/settings.py` → `config/settings/{base,development,production}.py`.
- `base.py`: everything shared — apps, DRF, JWT, CORS, Celery, cache, logging
- `development.py`: `DEBUG=True`, permissive CORS
- `production.py`: `DEBUG=False`, refuses to boot without a real
  `SECRET_KEY` (verified this actually raises), HSTS/secure cookies/SSL
  redirect, JSON-only renderer (browsable API is a dev convenience)

`manage.py`, `wsgi.py`, `asgi.py` default to `config.settings.development`;
override via `DJANGO_SETTINGS_MODULE` env var (Docker Compose does this).

### 7. API versioning
All API routes moved under **`/api/v1/`** (was `/api/`). Aggregated in
`config/api_v1_urls.py` so a future `/api/v2/` can be added as a sibling
file without touching v1 or any app. **The frontend's `NEXT_PUBLIC_API_URL`
default and `.env.example` were updated to match** — confirmed working
end-to-end (ran both servers together, loaded real pages).

### 8. DRF foundation
- Global throttling: `AnonRateThrottle` (100/min), `UserRateThrottle`
  (300/min), plus an `otp_request` scope (5/hour) pre-wired for Phase 2's
  OTP endpoints
- Existing global exception handler (`apps.shared.exceptions`) unchanged —
  already produced a consistent `{"detail", "code"}` shape
- `drf-spectacular` schema/docs unchanged, still at `/api/schema/` and
  `/api/docs/`

### 9. Docker infrastructure
- `Dockerfile` — multi-stage (builder/runtime), non-root user, gunicorn
- `docker-compose.yml` — **development**: backend (runserver, live-reload
  volume), postgres 16, redis 7, celery_worker, celery_beat, nginx
- `docker-compose.prod.yml` — **production**: gunicorn, migrate +
  collectstatic on boot, required env vars fail loudly if unset
  (`${VAR:?message}`), restart policies, no live-reload volumes
- `nginx/nginx.dev.conf` / `nginx.prod.conf` — static/media serving +
  reverse proxy; prod adds gzip + security headers
- **Caveat**: Docker itself isn't installable in this sandbox, so the
  Dockerfile/compose files are carefully hand-verified (YAML syntax
  checked, image/command choices cross-referenced against the actual
  settings) but **not build-tested**. First thing to run yourself:
  `docker compose build && docker compose up`.

### 10. Code quality
- `pyproject.toml` — ruff + black + isort, line-length 110, py312 target
- `.pre-commit-config.yaml` — ruff (autofix), black, isort, trailing
  whitespace/EOF/yaml/large-file/merge-conflict hooks
- Ran all three tools across the entire codebase now, not just configured
  them: `ruff check .` → clean, `black .` → 19 files reformatted,
  `isort .` → clean. Re-ran the full test suite after formatting to
  confirm nothing broke.

## Migration list (fresh, post-rename)

```
accounts/0001_initial.py
locations/0001_initial.py
brand/0001_initial.py
category/0001_initial.py
products/0001_initial.py
cart/0001_initial.py
media/0001_initial.py
orders/0001_initial.py
site_settings/0001_initial.py
```
(plus Django's own `admin`, `auth`, `contenttypes`, `sessions` migrations,
unchanged)

## Commands to run

```bash
# Local, no Docker
cp .env.example .env                 # edit SECRET_KEY etc.
pip install -r requirements/development.txt
python manage.py migrate
python manage.py seed_demo_data      # admin/admin12345 + sample catalog
python manage.py runserver

# Docker, local dev
cp .env.example .env
docker compose build
docker compose up
# in another shell, one-time:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data

# Docker, production
cp .env.example .env   # fill in every required var, especially SECRET_KEY,
                        # ALLOWED_HOSTS, DATABASE_URL, POSTGRES_PASSWORD,
                        # CORS_ALLOWED_ORIGINS
docker compose -f docker-compose.prod.yml up -d

# Code quality
ruff check .
black .
isort .
pre-commit install     # to run these automatically on every commit
```

## Testing instructions

```bash
python manage.py test                 # all 42 tests, unchanged behavior
python manage.py test apps.orders     # single app
python manage.py check --deploy       # production readiness check
```

Celery was verified for real, not just configured: started a worker
(`celery -A config worker`), submitted `apps.shared.tasks.ping`, confirmed
the worker received it, executed it, and returned `"pong"` through Redis.

## What Phase 1 deliberately does NOT include

- Repository pattern — not introduced anywhere yet. The spec asked for it
  "where useful"; nothing in the current codebase has query complexity that
  benefits from a repository layer over what selectors.py already gives.
  If Phase 3+ inventory reservation logic needs it, it'll be added there,
  scoped to that one problem.
- Real models/business logic for `inventory`, `delivery`, `pickup_points`,
  `payments`, `wallet`, `loyalty`, `notifications`, `reviews`, `support` —
  intentionally scaffolded only (see item 4 above).
- Any change to existing response shapes, URL paths (beyond the `/v1/`
  prefix), or business rules in products/cart/orders/accounts.

## Full file change summary

**Renamed directories:** `apps/core`→`shared`, `apps/users`→`accounts`,
`apps/categories`→`category`, `apps/brands`→`brand`

**New files:** `config/settings/{__init__,base,development,production}.py`,
`config/celery.py`, `config/api_v1_urls.py`, `apps/shared/{constants,
validators,response,tasks}.py`, `{selectors,permissions,signals,tasks}.py`
in every one of the 10 working apps, full skeletons for the 9 scaffold
apps, `Dockerfile`, `.dockerignore`, `docker-compose.yml`,
`docker-compose.prod.yml`, `nginx/nginx.{dev,prod}.conf`, `pyproject.toml`,
`.pre-commit-config.yaml`, `requirements/{base,development,production}.txt`

**Removed:** `config/settings.py`, `config/urls.py` (rewritten), old
`requirements.txt`, all pre-rename migration files

**Modified:** every app's `views.py`→`api/views.py` (selector-based
queries), `admin.py` (import paths only), `tests.py` (namespace-safe,
unchanged assertions), root `README.md`
