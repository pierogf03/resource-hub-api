# Resource Hub Backend

API REST para gestionar recursos externos, asignaciones, proveedores, iniciativas, ?rdenes de compra mensuales, dashboard, importaci?n hist?rica desde Excel e integraci?n del asistente IA Resource Hub Assistant v?a Workato.

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- JWT (python-jose)
- bcrypt
- openpyxl
- httpx

## Instalaci?n

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Configura `DATABASE_URL`, `JWT_SECRET_KEY` y las variables de Workato/IA en `.env`.

## Base de datos

Crea la base de datos PostgreSQL `resource_hub` y ejecuta:

```bash
alembic upgrade head
python -m app.seed.seed_data
```

## Ejecuci?n

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger: http://localhost:8000/docs

## Autenticaci?n

1. Si no hay usuarios, registra el primero con `POST /auth/register`.
2. Inicia sesi?n con `POST /auth/login`.
3. Usa el token Bearer en los dem?s endpoints.

Usuarios demo (despu?s del seed):

| Email | Password | Rol |
|-------|----------|-----|
| admin@resorusehub.com | Admin123 | ADMIN |
| manager1@resorusehub.com | Manager123 | MANAGER |
| analyst1@resorusehub.com | Analyst123 | ANALYST |

## Endpoints principales

| M?dulo | Rutas |
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
| Resource Hub Assistant | `/ai/chat/messages`, `/ai/chat/actions/confirm` |
| Workato Internal | `/internal/workato/*` |

## Resource Hub Assistant

Arquitectura final por API:

```
Angular ? POST /ai/chat/messages ? FastAPI ? Workato API ? Skills ? /internal/workato ? PostgreSQL
```

- Angular **nunca** llama directamente a Workato ni guarda API keys de Workato.
- FastAPI es el ?nico componente que conoce `WORKATO_AI_CHAT_URL` y `WORKATO_AI_CHAT_API_KEY`.
- Workato llama a Resource Hub solo por endpoints internos protegidos con `WORKATO_INTERNAL_API_KEY`.

### Endpoints de chat (JWT requerido)

**POST /ai/chat/messages**

```json
{
  "message": "?Qu? recursos est?n por vencer?",
  "conversation_id": "optional-string",
  "metadata": { "screen": "dashboard", "source": "resource-hub-web" }
}
```

**POST /ai/chat/actions/confirm**

```json
{
  "conversation_id": "conv-uuid",
  "action_id": "action-uuid",
  "approved": true,
  "rejection_reason": null
}
```

### Variables de entorno IA

| Variable | Descripci?n |
|----------|-------------|
| WORKATO_AI_CHAT_URL | Endpoint API de Workato para el Genie |
| WORKATO_AI_CHAT_API_KEY | API key para llamar a Workato (solo backend) |
| WORKATO_INTERNAL_API_KEY | API key que Workato usa en `/internal/workato` |
| AI_CHAT_ENABLED | Activa o desactiva el chat IA |
| AI_CHAT_AUDIT_ENABLED | Activa auditor?a de mensajes y acciones |
| AI_CHAT_TIMEOUT_SECONDS | Timeout de llamada a Workato |
| AI_CHAT_MAX_MESSAGE_LENGTH | Longitud m?xima del mensaje del usuario |

### Skills soportadas

Consulta: `get_dashboard_summary`, `get_expiring_resources`, `search_assignments`, `get_purchase_orders_status`, `get_budget_summary`, `get_import_status`.

Acci?n (con confirmaci?n del usuario): `generate_monthly_purchase_orders`, `update_purchase_order_status`.

### Reglas de seguridad

- Permisos siempre validados en el backend por rol (ADMIN / MANAGER / ANALYST).
- Las acciones destructivas requieren confirmaci?n expl?cita v?a `/ai/chat/actions/confirm`.
- Toda interacci?n se audita en `ai_chat_audit_logs` cuando `AI_CHAT_AUDIT_ENABLED=true`.

## Importaci?n Excel

Sube un archivo `.xlsx` hist?rico a `POST /imports/historical-excel` con `multipart/form-data`.

Campos opcionales: `default_manager_id`, `default_exchange_rate`, `auto_generate_purchase_orders`.

## Documentaci?n completa

Ver [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md).
