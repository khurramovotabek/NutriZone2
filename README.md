# NutriZone — Backend

Production REST API for **NutriZone**, a sports nutrition marketplace.
Django 6 + Django REST Framework + PostgreSQL 16 + Redis + Celery.

See [`docs/PHASE_1_FOUNDATION.md`](docs/PHASE_1_FOUNDATION.md) for the full
write-up of the Phase 1 foundation upgrade (Django 6, app restructure,
Docker, settings split, API versioning, code quality tooling) including
exactly what changed and why.

## Stack

- Python 3.12, Django 6, Django REST Framework
- PostgreSQL 16 (SQLite fallback for local dev without Docker)
- Redis (cache + Celery broker/result backend)
- Celery (worker + beat, wired and verified end-to-end)
- JWT auth (`djangorestframework-simplejwt`)
- UUID primary keys everywhere
- `drf-spectacular` for OpenAPI schema + Swagger docs
- Docker Compose for both development and production

## Architecture

Each domain lives in its own app under `apps/`, following a consistent
service-layer structure:

```
apps/<domain>/
  models.py        # DB schema
  services.py       # business logic (no Repository/CQRS unless a domain
                     # genuinely needs it -- see docs/PHASE_1_FOUNDATION.md)
  selectors.py       # read-query construction, kept separate from views
  permissions.py      # domain permission classes
  signals.py
  tasks.py            # Celery tasks
  admin.py
  tests.py
  api/
    serializers.py
    views.py           # thin HTTP layer, delegates to services/selectors
    urls.py
    filters.py          # where relevant
```

### Working apps

| App | Responsibility |
|---|---|
| `shared` | Base model (UUID + timestamps), pagination, permissions, exceptions, constants, validators, response helpers |
| `accounts` | Custom user model, auth (JWT), profile |
| `locations` | Country / Region / City reference data (used by brands + checkout) |
| `category` | Product categories -- unlimited-depth tree (adjacency list + materialized path), mega-menu tree endpoint, breadcrumbs |
| `brand` | Product brands (each with an optional country of origin) |
| `products` | Products, images, variants, specifications, search/filtering |
| `cart` | Guest + authenticated shopping cart |
| `orders` | Checkout, order workflow (NEW → PENDING → ACCEPTED / CANCELLED) |
| `media` | General-purpose admin media uploads |
| `dashboard` | Admin statistics/overview |
| `site_settings` | Singleton storefront configuration |
| `reviews` | Ratings, photo/video review media, admin replies (with notification), helpful votes, reporting |
| `notifications` | Per-user notifications (order updates, promotions, admin messages, review replies); admin can broadcast to all/selected users |

### Scaffolded apps (structure only, no business logic yet)

`inventory`, `delivery`, `pickup_points`, `payments`, `wallet`, `loyalty`,
`notifications`, `reviews`, `support` — registered and ready, each
`models.py` docstring says which upcoming phase fills it in.

### Key business rules encoded in the services layer

- **Inventory lives on `ProductVariant`, never on `Product`.**
- **Stock is only decremented when an order moves to `PENDING`** — not at
  checkout. Cancelling a `PENDING`/`ACCEPTED` order restocks it automatically.
- **`OrderItem` stores an immutable snapshot** (product name, variant name,
  price, SKU) so historical orders never change even if the catalog does.
- **Checkout requires a structured delivery location** — `country` → `region`
  → `city` (validated to belong to each other), plus a free-text
  `delivery_address` line for street/building detail.
- **Guest carts** are identified by a `Cart` UUID sent via the `X-Cart-Id`
  header; logged-in users get a persistent cart tied to their account.

## Getting started

Admin panel uses [django-jazzmin](https://github.com/farridav/django-jazzmin) with
NutriZone branding (graphite background, volt-green accent — matches the storefront).
A custom stats dashboard lives at `/admin/dashboard/` (linked from the sidebar),
reusing the same `DashboardService` that powers the API's overview endpoint.


### Without Docker

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements/development.txt

cp .env.example .env             # edit SECRET_KEY at minimum
# Leave DATABASE_URL unset to use local SQLite; needs Redis running locally
# for cache/throttling to work (`redis-server`, or see Docker option below).

python manage.py migrate
python manage.py seed_demo_data  # optional: admin/admin12345 + sample catalog
python manage.py runserver
```

### With Docker (recommended — matches production topology)

```bash
cp .env.example .env
docker compose build
docker compose up
# first time only, in another shell:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data
```

This starts Postgres 16, Redis, the Django backend, a Celery worker, Celery
beat, and Nginx (proxying to the backend at `http://localhost:8080`).

API: `http://localhost:8000/api/v1/` (or `:8080` through Nginx).
Interactive docs: `/api/docs/`. Django admin: `/admin/`.

## Running tests

```bash
python manage.py test
```

42 tests cover catalog search/filtering, stock validation, the full order
status workflow (including restocking on cancellation), cart behavior for
both guests and authenticated users, location cascading validation, and
permission boundaries.

## Code quality

```bash
ruff check .      # lint
black .           # format
isort .           # import order
pre-commit install  # run all of the above automatically on commit
```

## API overview

All endpoints are under **`/api/v1/`**.

| Endpoint | Notes |
|---|---|
| `POST auth/register/`, `auth/login/`, `auth/login/refresh/` | JWT auth |
| `GET/PATCH auth/me/` | Current user profile |
| `GET/POST/PATCH/DELETE categories/`, `brands/` | Public read, admin write |
| `GET categories/tree/` | Full nested category tree (cached), for the mega menu / mobile accordion |
| `GET categories/{slug}/breadcrumbs/` | Root-to-self ancestor chain |
| `POST categories/{slug}/move/` | Admin-only re-parent, cascades to all descendants |
| `GET/POST/PATCH/DELETE locations/countries/`, `regions/?country=`, `cities/?region=` | Public read, admin write — dropdown data for checkout |
| `GET/POST/PATCH/DELETE products/` | Search (`?search=`), filters (`?category=`, `?brand=`, `?min_price=`, `?max_price=`, `?availability=`), sort (`?sort=`) |
| `.../products/{slug}/images/`, `/variants/`, `/specifications/` | Nested admin management |
| `GET/POST cart/`, `cart/items/...` | Guest (via `X-Cart-Id` header) or authenticated |
| `POST orders/` | Checkout — turns the caller's cart into an order |
| `PATCH orders/{id}/status/` | Admin-only status transitions |
| `GET dashboard/overview/` | Admin statistics |
| `GET/PATCH settings/` | Storefront-wide settings (singleton) |
| `.../media/` | Admin media library (validated uploads) |

## Security notes

- SKU/barcode uniqueness enforced at DB and serializer level
- Media uploads validated by extension and size
- Global API throttling (100/min anon, 300/min authenticated)
- Production security headers (HSTS, secure cookies, SSL redirect, JSON-only
  responses) auto-enable under `config.settings.production`
- Production settings refuse to boot with the default `SECRET_KEY`
- Never commit `.env` — only `.env.example` is tracked

## Roadmap (see docs/PHASE_1_FOUNDATION.md for full detail)

- **Phase 2** — Phone + OTP auth, mandatory verified email
- **Phase 3** — Order status history, inventory reservation
- **Phase 4** — Wallet, loyalty cashback tariffs, delivery, pickup points, payments
- **Phase 5** — Notifications, reviews, support/call center
