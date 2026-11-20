# Vehicle API (Django REST Framework + PostgreSQL + JWT)

## Setup
```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # then set DJANGO_SECRET_KEY and DB_PASSWORD
# create an empty PostgreSQL database named vehicles_db (pgAdmin or createdb)
.\venv\Scripts\python manage.py migrate
.\venv\Scripts\python manage.py createsuperuser   # optional, for /admin/
.\venv\Scripts\python manage.py runserver
```

## Project layout
| App | Purpose |
|---|---|
| `config/` | settings, root URLs |
| `core/` | shared building blocks: `TimeStampedModel`, `AuditedModel` (created_by / updated_by), `AuditedModelViewSet`, admin mixin, JSON exception handler |
| `users/` | custom email-based `User` model, signup / login / profile, JWT |
| `vehicles/` | `Make` and `Vehicle` APIs |

## Authentication
JWT (Bearer tokens). Every endpoint except signup, login and token refresh requires
`Authorization: Bearer <access token>`. Signup, login and refresh are rate-limited
(`AUTH_THROTTLE_RATE`, default 10/minute per IP).

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/user/signup/` | no | `email, password, password_confirm, first_name?, last_name?` → `{user, tokens}` |
| POST | `/api/v1/user/login/` | no | `email, password` → `{user, tokens}` |
| POST | `/api/v1/user/token/refresh/` | no | `refresh` → new `access` |
| GET / PATCH | `/api/v1/user/` | yes | own profile (`email, first_name, last_name`) |

Access tokens last `JWT_ACCESS_TOKEN_MINUTES` (30), refresh tokens `JWT_REFRESH_TOKEN_DAYS` (7).
In the browsable API you can also log in with the **Log in** link (`/api-auth/login/`).

## Make & Vehicle endpoints (authenticated)
| Method | URL | Action |
|---|---|---|
| GET / POST | `/api/v1/make/` | list / create make (multipart for `logo`) |
| GET / PATCH / DELETE | `/api/v1/make/<id>/` | retrieve / update / delete |
| GET / POST | `/api/v2/vehicle/` | list / create vehicle (multipart for `image`) |
| GET / PATCH / DELETE | `/api/v2/vehicle/<id>/` | retrieve / update / delete |

`created_by` / `updated_by` are filled in from the logged-in user and cannot be set by the client.

## Filters
- **Make:** `?name=toy`, `?founded_after=1940-01-01`, `?founded_before=2000-01-01`, `?created_by=<user id>`, `?search=`, `?ordering=-founded_at`
- **Vehicle:** `?make=1`, `?make_name=hon`, `?name=`, `?model=`, `?color=black`, `?engine=1500`, `?engine_min=1000&engine_max=2000`, `?created_by=<user id>`, `?search=`, `?ordering=engine`
- Pagination: `?page=2` (10 per page)

## Tests
```powershell
.\venv\Scripts\python manage.py test
```
