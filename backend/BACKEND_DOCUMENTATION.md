# Resource Hub Backend — Documentación Técnica

## 1. Nombre del proyecto

Resource Hub Backend

## 2. Descripción

API REST para gestionar recursos externos, asignaciones, proveedores, iniciativas, órdenes de compra mensuales, dashboard, importación histórica desde Excel e integración del asistente conversacional Resource Hub Assistant vía API de Workato/Genie.

## 3. Stack utilizado

- FastAPI — framework HTTP y documentación OpenAPI
- PostgreSQL — base de datos relacional
- SQLAlchemy — ORM
- Alembic — migraciones
- JWT (python-jose) — autenticación stateless
- bcrypt — hash de contraseñas
- Pydantic — validación de datos
- openpyxl — lectura de archivos Excel
- httpx — cliente HTTP para integración Workato

## 4. Arquitectura de carpetas

```
backend/app/
  core/         Configuración, DB, seguridad, excepciones
  models/       Modelos SQLAlchemy (10 tablas)
  schemas/      DTOs Pydantic request/response
  routers/      Endpoints HTTP
  services/     Lógica de negocio
  repositories/ Acceso a datos
  utils/        Utilidades (fechas, montos, Excel, strings, permisos)
  seed/         Datos demo
```

Flujo: `routers` → `services` → `repositories` → `models`.

## 5. Modelo de datos

| Tabla | Descripción |
|-------|-------------|
| app_users | Usuarios del sistema (ADMIN, MANAGER, ANALYST) |
| providers | Empresas proveedoras configurables |
| initiatives | Proyectos/iniciativas |
| external_resources | Consultores externos |
| resource_assignments | Asignaciones/contrataciones |
| resource_assignment_initiatives | Asignación parcial a múltiples iniciativas |
| purchase_orders | Órdenes de compra mensuales |
| import_batches | Lotes de importación Excel |
| import_batch_errors | Errores por fila de importación |
| ai_chat_audit_logs | Auditoría del Resource Hub Assistant |

Todas las tablas usan UUID como primary key (excepto campos string en auditoría IA).

## 6. Reglas de negocio

### Cálculo de costos en USD

- Si `currency = USD`: `monthly_cost_usd = monthly_cost`
- Si `currency = PEN`: `monthly_cost_usd = monthly_cost / exchange_rate` (tipo de cambio obligatorio)
- `total_cost_usd = monthly_cost_usd * duration_months`

### Generación mensual de OCs

- Una OC por cada mes dentro del rango `start_date`–`end_date`
- `period_month` = primer día del mes
- `provider_id` se obtiene de la asignación, no del input del cliente
- No se permiten OCs duplicadas para el mismo mes y asignación

### Semáforo de vencimiento

- GREEN: más de 30 días hasta `end_date`
- AMBER: entre 15 y 30 días
- RED: menos de 15 días o vencido

### Filtro por manager

- ADMIN: ve todo
- MANAGER: solo asignaciones donde `manager_id` es su user_id
- ANALYST: solo asignaciones donde `analyst_responsible_id` es su user_id

### Importación histórica desde Excel

- Columnas esperadas: Proyecto, Consultor, Analista responsable, Proveedor, Perfil, costos, duración, fechas, Mes1–Mes8
- Errores por fila sin detener toda la carga
- Creación/reutilización automática de proveedores, iniciativas y recursos

## 7. Tratamiento de proveedores

- Los proveedores son configurables (no hay catálogo cerrado)
- Se crean manualmente por API o automáticamente en importación Excel
- Deduplicación por nombre normalizado (trim + case-insensitive)
- Los nombres del seed son ficticios y solo para demo
- No se usan empresas reales no proporcionadas

## 8. Perfiles técnicos

- Se almacenan en `external_resources.technical_profile`
- Perfiles demo: ABAP, FI, Full Stack, Workato, BW, QA, Data, Integraciones SAP, Backend Python, Frontend Angular
- El perfil técnico describe la especialidad del consultor
- El proveedor es la empresa que suministra al recurso

## 9. Endpoints

### Auth

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /auth/register | Crear usuario (primer usuario sin auth; luego solo ADMIN) |
| POST | /auth/login | Login y obtención de JWT |
| GET | /auth/me | Usuario autenticado actual |

### Users (ADMIN)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /users | Listar usuarios paginados |
| POST | /users | Crear usuario |

### Providers

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /providers | Listar proveedores |
| POST | /providers | Crear proveedor |
| PUT | /providers/{id} | Actualizar proveedor |

### Initiatives

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /initiatives | Listar iniciativas |
| POST | /initiatives | Crear iniciativa |

### External Resources

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /external-resources | Listar recursos |
| POST | /external-resources | Crear recurso |
| PUT | /external-resources/{id} | Actualizar recurso |

### Assignments

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /assignments | Listar asignaciones (filtrado por rol) |
| POST | /assignments | Crear asignación |
| POST | /assignments/{id}/generate-monthly-purchase-orders | Generar OCs mensuales |

### Purchase Orders

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /purchase-orders | Listar OCs |
| POST | /purchase-orders | Crear OC |
| PUT | /purchase-orders/{id} | Actualizar OC |

### Dashboard

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /dashboard/summary | Resumen agregado |
| GET | /dashboard/expiring-resources | Recursos próximos a vencer |

### Imports

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /imports/historical-excel | Importar Excel histórico |
| GET | /imports | Listar lotes de importación |
| GET | /imports/{batch_id}/errors | Errores de un lote |

### Resource Hub Assistant (JWT)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /ai/chat/messages | Enviar mensaje al asistente vía Workato |
| POST | /ai/chat/actions/confirm | Confirmar o rechazar acción pendiente |

### Workato Internal (API key + X-ResourceHub-User-Id)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /internal/workato/dashboard-summary | Resumen del área |
| GET | /internal/workato/expiring-resources | Recursos por vencer |
| GET | /internal/workato/assignments | Búsqueda de asignaciones |
| GET | /internal/workato/purchase-orders | Estado de OCs |
| GET | /internal/workato/budget-summary | Presupuesto comprometido |
| GET | /internal/workato/import-status | Última importación |
| POST | /internal/workato/assignments/{id}/generate-monthly-purchase-orders | Generar OCs (skill interna) |
| PUT | /internal/workato/purchase-orders/{id}/status | Actualizar estado OC (skill interna) |

Todas las respuestas usan el formato `{ success, message, data }` o `{ success, message, errors }`.

## 10. Seguridad

- Login con email/password; contraseñas hasheadas con bcrypt
- JWT Bearer con claims `user_id`, `email`, `role`
- Dependencias: `get_current_user`, `require_admin`, `require_manager_or_admin`, `verify_workato_internal`
- `password_hash` nunca se devuelve en respuestas
- Workato internal: `Authorization: Bearer {WORKATO_INTERNAL_API_KEY}` + header `X-ResourceHub-User-Id`
- El rol del usuario se resuelve siempre desde la base de datos; no se confía en datos enviados por Workato

## 11. Importación Excel

**Columnas requeridas:** Proyecto, Consultor, Analista responsable, Proveedor, Perfil, Costo Mensual [USD], Costo Mensual [PEN], Duración, Costo Total [USD], Costo Total [PEN], Inicio, Fin, Comentarios, Mes1–Mes8.

**Mapeo de estados OC:** Pendiente→PENDING, Coupa generado→COUPA_GENERATED, OC enviada/Enviada→SENT, Aprobada→APPROVED, Cerrada→CLOSED.

**Reglas de moneda:** USD si Costo Mensual [USD] > 0; si no, PEN con `default_exchange_rate`.

## 12. Variables de entorno

| Variable | Descripción |
|----------|-------------|
| DATABASE_URL | Conexión PostgreSQL |
| JWT_SECRET_KEY | Clave secreta JWT |
| JWT_ALGORITHM | Algoritmo (HS256) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Expiración del token |
| APP_NAME | Nombre de la aplicación (Resource Hub) |
| APP_ENV | Entorno (development/production) |
| CORS_ORIGINS | Orígenes CORS permitidos |
| WORKATO_AI_CHAT_URL | Endpoint API de Workato para el Genie |
| WORKATO_AI_CHAT_API_KEY | API key para llamar a Workato desde FastAPI |
| WORKATO_INTERNAL_API_KEY | API key que Workato usa en endpoints internos |
| AI_CHAT_ENABLED | Activa o desactiva el chat IA |
| AI_CHAT_AUDIT_ENABLED | Activa auditoría de mensajes y acciones |
| AI_CHAT_TIMEOUT_SECONDS | Timeout máximo de llamada a Workato |
| AI_CHAT_MAX_MESSAGE_LENGTH | Longitud máxima del mensaje del usuario |

## 13. Integración Workato / Resource Hub Assistant

### Arquitectura final por API

```
Angular → POST /ai/chat/messages → FastAPI → Workato API Endpoint
Workato → Skills → GET/POST /internal/workato → PostgreSQL
FastAPI → respuesta al frontend
```

Esta es la arquitectura final del chat IA. FastAPI actúa como proxy seguro: el frontend nunca conoce credenciales de Workato.

### Payload enviado a Workato

FastAPI envía a `WORKATO_AI_CHAT_URL`:

- `message`, `conversation_id` (opcional)
- `user`: `{ id, full_name, email, role }` — sin password ni JWT
- `resource_hub_context`: capacidades permitidas y modo `backend_enforced`
- `metadata`: pantalla, timestamp, etc.

### Respuesta esperada de Workato

JSON con: `conversation_id`, `reply`, `intent`, `used_skills`, `suggested_questions`, `requires_confirmation`, `pending_action` (opcional).

Si `requires_confirmation=true`, el frontend debe llamar `POST /ai/chat/actions/confirm` antes de ejecutar cambios reales en el sistema.

### Confirmación de acciones

Acciones soportadas:

1. `generate_monthly_purchase_orders` — payload: `assignment_id`, `overwrite_existing`
2. `update_purchase_order_status` — payload: `purchase_order_id`, `status`, `comments`, `po_number`

Permisos:

- Generar OCs: ADMIN y MANAGER (con acceso a la asignación)
- Actualizar estado OC: ADMIN, MANAGER y ANALYST (con acceso a la asignación de la OC)

### Auditoría

Tabla `ai_chat_audit_logs`. Eventos:

- `CHAT_MESSAGE_SENT`, `CHAT_MESSAGE_RESPONSE`, `CHAT_MESSAGE_FAILED`
- `CHAT_ACTION_PENDING`, `CHAT_ACTION_APPROVED`, `CHAT_ACTION_REJECTED`
- `CHAT_ACTION_EXECUTED`, `CHAT_ACTION_FAILED`

### Manejo de errores del asistente

| Caso | HTTP | Mensaje |
|------|------|---------|
| AI_CHAT_ENABLED=false | 503 | Resource Hub Assistant is disabled |
| Timeout Workato | 504 | The assistant is taking too long to respond |
| 401/403 Workato | 502 | Assistant authentication failed |
| 500 Workato | 502 | Assistant service error |
| Respuesta inválida | 502 | Invalid assistant response |

## 14. Cómo ejecutar localmente

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed.seed_data
uvicorn app.main:app --reload --port 8000
```

## 15. Datos seed

Ejecutar `python -m app.seed.seed_data` después de las migraciones. Carga 6 usuarios, 5 proveedores demo, 5 iniciativas, 10 consultores, 10 asignaciones y OCs mensuales con estados variados.

## 16. Decisiones técnicas

- **FastAPI:** rendimiento, tipado, Swagger automático
- **PostgreSQL:** robustez relacional, compatible con Supabase
- **JWT:** autenticación stateless para frontend Angular
- **SQLAlchemy:** ORM maduro con migraciones Alembic
- **openpyxl:** lectura nativa de archivos .xlsx del Excel histórico
- **httpx:** integración síncrona con Workato sin retries automáticos (evita duplicar acciones)

## 17. Limitaciones actuales

- No hay frontend Angular conectado en este repositorio
- No hay integración real con Coupa
- La receta Workato/Genie debe configurarse externamente apuntando a `/internal/workato`
- No hay envío de notificaciones ni reportes PDF

## 18. Próximos pasos

- Conectar frontend Angular al chat
- Configurar receta Workato con skills documentadas
- Agregar reportes ejecutivos
- Agregar pruebas automatizadas completas
