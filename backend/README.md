# Resoruse Hub Backend

API REST para gestionar recursos externos, asignaciones, proveedores, iniciativas, órdenes de compra mensuales, dashboard e importación histórica desde Excel.

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- JWT (python-jose)
- bcrypt
- openpyxl

## Instalación

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Configura `DATABASE_URL` y `JWT_SECRET_KEY` en `.env`.

## Base de datos

Crea la base de datos PostgreSQL `resource_hub` y ejecuta:

```bash
alembic upgrade head
python -m app.seed.seed_data
```

## Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger: http://localhost:8000/docs

## Autenticación

1. Si no hay usuarios, registra el primero con `POST /auth/register`.
2. Inicia sesión con `POST /auth/login`.
3. Usa el token Bearer en los demás endpoints.

Usuarios demo (después del seed):

| Email | Password | Rol |
|-------|----------|-----|
| admin@resorusehub.com | Admin123 | ADMIN |
| manager1@resorusehub.com | Manager123 | MANAGER |
| analyst1@resorusehub.com | Analyst123 | ANALYST |

## Endpoints principales

| Módulo | Rutas |
|--------|-------|
| Auth | `/auth/register`, `/auth/login`, `/auth/me` |
| Users | `/users` |
| Providers | `/providers` |
| Initiatives | `/initiatives` |
| External Resources | `/external-resources` |
| Assignments | `/assignments`, `/assignments/{id}/generate-monthly-purchase-orders` |
| Purchase Orders | `/purchase-orders` |
| Dashboard | `/dashboard/summary`, `/dashboard/expiring-resources` |
| Imports | `/imports/historical-excel`, `/imports`, `/imports/{batch_id}/errors` |

## Importación Excel

Sube un archivo `.xlsx` histórico a `POST /imports/historical-excel` con `multipart/form-data`.

Campos opcionales: `default_manager_id`, `default_exchange_rate`, `auto_generate_purchase_orders`.

## Documentación completa

Ver [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md).
