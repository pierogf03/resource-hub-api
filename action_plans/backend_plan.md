PLAN CONSOLIDADO PARA CURSOR — BACKEND Resoruse Hub

Quiero construir únicamente el BACKEND de una aplicación web llamada Resoruse Hub.

Resoruse Hub es una plataforma para reemplazar un Excel de control de recursos externos. El sistema debe permitir gestionar consultores externos, proveedores, iniciativas/proyectos, asignaciones, costos, fechas de inicio y fin, vencimientos, órdenes de compra mensuales, dashboard e importación histórica desde Excel.

El backend debe estar desarrollado con prácticas profesionales, arquitectura ordenada, validaciones sólidas, autenticación segura con tokens JWT y documentación clara en archivos .md.

IMPORTANTE:
Construir el proyecto sin errores, con estructura profesional, imports correctos, tipado claro, validaciones completas y endpoints funcionales. No dejar TODOs, código incompleto, rutas rotas, imports sin usar ni lógica duplicada.

============================================================

1. STACK OBLIGATORIO
   ============================================================

Usar:

* Python 3.12+
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Pydantic
* JWT para autenticación
* Passlib o bcrypt para hash de contraseñas
* python-dotenv o pydantic-settings para variables de entorno
* python-multipart para carga de archivos
* openpyxl para leer archivos Excel
* psycopg2 o asyncpg según la implementación elegida
* pytest opcional para pruebas básicas

Base de datos:

* PostgreSQL local para desarrollo.
* Compatible con Supabase PostgreSQL para despliegue posterior.

============================================================
2. ALCANCE ACTUAL DEL BACKEND
=============================

Por ahora el backend debe incluir solo estos módulos:

1. Autenticación y seguridad
2. Usuarios
3. Proveedores
4. Iniciativas / proyectos
5. Recursos externos
6. Asignaciones de recursos
7. Órdenes de compra mensuales
8. Dashboard resumen
9. Importación histórica desde Excel
10. Documentación técnica en archivos .md

No implementar todavía:

* Frontend
* IA / Workato GO
* Integración real con Coupa
* Envío de correos
* Notificaciones automáticas
* Reportes PDF

============================================================
3. CONTEXTO DEL EXCEL ACTUAL
============================

El sistema reemplaza un Excel con columnas como:

* Proyecto
* Consultor
* Analista responsable
* Proveedor
* Perfil
* Costo Mensual [USD]
* Costo Mensual [PEN]
* Duración
* Costo Total [USD]
* Costo Total [PEN]
* Inicio
* Fin
* Comentarios
* Mes1
* Mes2
* Mes3
* Mes4
* Mes5
* Mes6
* Mes7
* Mes8

Regla importante de negocio:

Un mismo recurso puede tener más de una OC durante su asignación. Por lo general, las OCs son mensuales. Si un recurso está asignado o contratado por 3 meses, debe tener 3 órdenes de compra, una por cada mes.

No modelar Mes1, Mes2, Mes3 como columnas fijas. Cada OC mensual debe ser un registro en la tabla purchase_orders.

============================================================
4. CRITERIOS IMPORTANTES SOBRE PROVEEDORES Y PERFILES
=====================================================

No usar empresas reales o nombres inventados que no hayan sido proporcionados explícitamente.

El reto indica que para cada recurso externo se debe registrar:

* Nombre del consultor
* Empresa proveedora
* Perfil técnico
* Proyecto o iniciativa asociada
* Analista responsable
* Fechas de inicio y fin
* Costos
* OCs mensuales
* Observaciones

Los perfiles técnicos de referencia son:

* ABAP
* FI
* Full Stack
* Workato
* BW
* QA
* Data
* Integraciones SAP
* Backend Python
* Frontend Angular

Reglas sobre proveedores:

* No hardcodear proveedores reales como NTT Data, Globant, Indra, Softtek, Accenture, IBM u otros.
* No crear un enum cerrado de proveedores.
* Los proveedores deben ser configurables.
* Los proveedores pueden crearse manualmente por API.
* Los proveedores pueden crearse automáticamente durante la importación histórica desde Excel.
* Si durante la importación aparece un proveedor que ya existe por nombre, reutilizarlo.
* Si no existe, crearlo.
* Normalizar el nombre quitando espacios al inicio y al final.
* Evitar duplicados por diferencias simples de mayúsculas/minúsculas.

Ejemplo:

"proveedor abc"
"Proveedor ABC"
" PROVEEDOR ABC "

Deben tratarse como el mismo proveedor.

Para seed data usar nombres genéricos de demo, por ejemplo:

* Proveedor Demo SAP
* Proveedor Demo Workato
* Proveedor Demo Full Stack
* Proveedor Demo BW
* Proveedor Demo Data Analytics

Estos nombres deben documentarse como datos ficticios.

============================================================
5. ESTRUCTURA DEL PROYECTO
==========================

Crear esta estructura:

backend/
app/
main.py

```
core/
  config.py
  database.py
  security.py
  exceptions.py

models/
  user.py
  provider.py
  initiative.py
  external_resource.py
  resource_assignment.py
  purchase_order.py
  import_batch.py

schemas/
  auth_schema.py
  user_schema.py
  provider_schema.py
  initiative_schema.py
  external_resource_schema.py
  assignment_schema.py
  purchase_order_schema.py
  dashboard_schema.py
  import_schema.py
  common_schema.py

routers/
  auth.py
  users.py
  providers.py
  initiatives.py
  external_resources.py
  assignments.py
  purchase_orders.py
  dashboard.py
  imports.py

services/
  auth_service.py
  user_service.py
  provider_service.py
  initiative_service.py
  external_resource_service.py
  assignment_service.py
  purchase_order_service.py
  dashboard_service.py
  excel_import_service.py

repositories/
  user_repository.py
  provider_repository.py
  initiative_repository.py
  external_resource_repository.py
  assignment_repository.py
  purchase_order_repository.py
  import_batch_repository.py

utils/
  date_utils.py
  money_utils.py
  excel_utils.py
  string_utils.py

seed/
  seed_data.py
```

alembic/
alembic.ini
requirements.txt
.env.example
README.md
BACKEND_DOCUMENTATION.md

============================================================
6. VARIABLES DE ENTORNO
=======================

Crear .env.example con:

DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/Resoruse Hub
JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_NAME=Resoruse Hub
APP_ENV=development
CORS_ORIGINS=http://localhost:4200

============================================================
7. MODELO DE DATOS
==================

Usar UUID como primary key en todas las tablas.

---

## 7.1 app_users

Representa usuarios del sistema: administradores, managers y analistas.

Campos:

* id UUID PK
* full_name VARCHAR(150) NOT NULL
* email VARCHAR(150) UNIQUE NOT NULL
* password_hash VARCHAR(255) NOT NULL
* role VARCHAR(30) NOT NULL
* is_active BOOLEAN DEFAULT TRUE
* created_at TIMESTAMP
* updated_at TIMESTAMP

Roles permitidos:

* ADMIN
* MANAGER
* ANALYST

Reglas:

* email debe ser único.
* password_hash nunca debe devolverse en respuestas.
* is_active controla si el usuario puede loguearse.

---

## 7.2 providers

Representa la empresa proveedora del recurso externo.

Campos:

* id UUID PK
* name VARCHAR(150) UNIQUE NOT NULL
* ruc VARCHAR(20) NULL
* contact_name VARCHAR(150) NULL
* contact_email VARCHAR(150) NULL
* is_active BOOLEAN DEFAULT TRUE
* created_at TIMESTAMP
* updated_at TIMESTAMP

Reglas:

* name es obligatorio.
* name debe normalizarse para evitar duplicados simples.
* ruc es opcional.
* contact_name es opcional.
* contact_email es opcional.
* No usar catálogo cerrado de proveedores.
* No hardcodear empresas reales.
* Los proveedores pueden venir desde el Excel o crearse por endpoint.

---

## 7.3 initiatives

Representa el proyecto o iniciativa.

Campos:

* id UUID PK
* name VARCHAR(180) UNIQUE NOT NULL
* description TEXT NULL
* responsible_manager_id UUID FK app_users.id NULL
* budget_usd NUMERIC(14,2) NULL
* is_active BOOLEAN DEFAULT TRUE
* created_at TIMESTAMP
* updated_at TIMESTAMP

Reglas:

* name obligatorio y único.
* budget_usd debe ser mayor o igual a 0 si se envía.
* responsible_manager_id debe existir si se envía.

---

## 7.4 external_resources

Representa al consultor externo como persona/recurso.

Campos:

* id UUID PK
* consultant_name VARCHAR(150) NOT NULL
* technical_profile VARCHAR(100) NOT NULL
* document_number VARCHAR(30) NULL
* is_active BOOLEAN DEFAULT TRUE
* created_at TIMESTAMP
* updated_at TIMESTAMP

Reglas:

* consultant_name obligatorio.
* technical_profile obligatorio.
* technical_profile describe la especialidad del consultor.
* No confundir technical_profile con provider.
* Para data demo usar perfiles alineados al reto: ABAP, FI, Full Stack, Workato, BW, QA, Data, Integraciones SAP.

---

## 7.5 resource_assignments

Representa la asignación o contratación de un recurso externo.

Campos:

* id UUID PK
* resource_id UUID FK external_resources.id NOT NULL
* provider_id UUID FK providers.id NOT NULL
* main_initiative_id UUID FK initiatives.id NOT NULL
* manager_id UUID FK app_users.id NOT NULL
* analyst_responsible_id UUID FK app_users.id NULL
* start_date DATE NOT NULL
* end_date DATE NOT NULL
* duration_months INTEGER NOT NULL
* monthly_cost NUMERIC(14,2) NOT NULL
* currency VARCHAR(3) NOT NULL
* exchange_rate NUMERIC(10,4) NULL
* monthly_cost_usd NUMERIC(14,2) NOT NULL
* total_cost_usd NUMERIC(14,2) NOT NULL
* status VARCHAR(30) DEFAULT 'ACTIVE'
* comments TEXT NULL
* created_at TIMESTAMP
* updated_at TIMESTAMP

Valores permitidos currency:

* USD
* PEN

Valores permitidos status:

* ACTIVE
* CLOSED
* CANCELLED

Reglas:

* resource_id debe existir.
* provider_id debe existir.
* main_initiative_id debe existir.
* manager_id debe existir.
* analyst_responsible_id debe existir si se envía.
* end_date >= start_date.
* duration_months > 0.
* monthly_cost >= 0.
* Si currency = PEN, exchange_rate es obligatorio y mayor a 0.
* Si currency = USD, exchange_rate puede ser NULL o 1.
* monthly_cost_usd se calcula desde el backend.
* total_cost_usd se calcula desde el backend.

Cálculos:

Si currency = USD:

monthly_cost_usd = monthly_cost

Si currency = PEN:

monthly_cost_usd = monthly_cost / exchange_rate

Costo total:

total_cost_usd = monthly_cost_usd * duration_months

---

## 7.6 resource_assignment_initiatives

Permite que un recurso esté asignado parcialmente a más de una iniciativa.

Campos:

* id UUID PK
* assignment_id UUID FK resource_assignments.id NOT NULL
* initiative_id UUID FK initiatives.id NOT NULL
* allocation_percentage NUMERIC(5,2) NOT NULL
* is_primary BOOLEAN DEFAULT FALSE
* is_funding_source BOOLEAN DEFAULT FALSE
* created_at TIMESTAMP

Reglas:

* allocation_percentage > 0 y <= 100.
* Una asignación solo puede tener una iniciativa principal.
* Una asignación solo puede tener una fuente de fondeo principal.
* La suma de allocation_percentage por assignment_id no debe exceder 100.
* La iniciativa principal debe coincidir con main_initiative_id o validarse de forma consistente.

---

## 7.7 purchase_orders

Representa las órdenes de compra mensuales.

Campos:

* id UUID PK
* assignment_id UUID FK resource_assignments.id NOT NULL
* provider_id UUID FK providers.id NOT NULL
* period_month DATE NOT NULL
* po_number VARCHAR(80) NULL
* status VARCHAR(30) DEFAULT 'PENDING'
* amount NUMERIC(14,2) NOT NULL
* currency VARCHAR(3) NOT NULL
* exchange_rate NUMERIC(10,4) NULL
* amount_usd NUMERIC(14,2) NOT NULL
* comments TEXT NULL
* created_at TIMESTAMP
* updated_at TIMESTAMP

Valores permitidos status:

* PENDING
* COUPA_GENERATED
* SENT
* APPROVED
* CLOSED
* CANCELLED

Reglas:

* Una asignación no puede tener más de una OC para el mismo period_month.
* period_month debe representar el primer día del mes.
* La OC debe estar dentro del rango start_date y end_date de la asignación.
* provider_id debe coincidir con el proveedor de la asignación.
* amount >= 0.
* Si currency = PEN, exchange_rate obligatorio y mayor a 0.
* amount_usd se calcula desde el backend.
* provider_id debe obtenerse desde la asignación y no confiar en input externo para evitar inconsistencias.

---

## 7.8 import_batches

Representa cada carga histórica desde Excel.

Campos:

* id UUID PK
* file_name VARCHAR(255) NOT NULL
* imported_by UUID FK app_users.id NOT NULL
* total_rows INTEGER DEFAULT 0
* successful_rows INTEGER DEFAULT 0
* failed_rows INTEGER DEFAULT 0
* status VARCHAR(30) DEFAULT 'PROCESSING'
* error_summary TEXT NULL
* created_at TIMESTAMP
* finished_at TIMESTAMP NULL

Valores permitidos status:

* PROCESSING
* COMPLETED
* COMPLETED_WITH_ERRORS
* FAILED

---

## 7.9 import_batch_errors

Representa errores por fila del Excel.

Campos:

* id UUID PK
* batch_id UUID FK import_batches.id NOT NULL
* row_number INTEGER NOT NULL
* column_name VARCHAR(120) NULL
* error_message TEXT NOT NULL
* raw_data JSONB NULL
* created_at TIMESTAMP

============================================================
8. AUTENTICACIÓN Y SEGURIDAD
============================

Implementar autenticación con JWT.

El login debe:

* Recibir email y password.
* Validar existencia del usuario.
* Validar que el usuario esté activo.
* Comparar password contra password_hash.
* Generar access_token.
* Incluir user_id, email y role en el token.
* Devolver datos básicos del usuario.
* Nunca devolver password_hash.

Implementar:

* get_current_user
* require_admin
* require_manager_or_admin

Todos los endpoints, excepto login y registro inicial, deben requerir Bearer Token.

Reglas de visibilidad:

* ADMIN puede ver todo.
* MANAGER solo puede ver asignaciones y recursos asociados a su manager_id.
* ANALYST puede ver recursos donde sea analyst_responsible_id.

============================================================
9. FORMATO ESTÁNDAR DE RESPUESTAS
=================================

Usar siempre respuestas consistentes.

Respuesta exitosa:

{
"success": true,
"message": "Operation completed successfully",
"data": {}
}

Respuesta de error:

{
"success": false,
"message": "Validation error",
"errors": [
{
"field": "email",
"message": "Invalid email format"
}
]
}

Para listados paginados:

{
"success": true,
"message": "Items retrieved successfully",
"data": {
"items": [],
"total": 0,
"page": 1,
"page_size": 10
}
}

============================================================
10. ENDPOINTS CON INPUT Y OUTPUT
================================

---

## 10.1 AUTH

POST /auth/register

Descripción:
Crear usuario inicial o usuarios desde ADMIN.

Input:

{
"full_name": "Maria Fernandez",
"email": "[maria@example.com](mailto:maria@example.com)",
"password": "Password123",
"role": "MANAGER"
}

Validaciones:

* full_name obligatorio.
* email válido y único.
* password mínimo 8 caracteres.
* role debe ser ADMIN, MANAGER o ANALYST.

Output 201:

{
"success": true,
"message": "User registered successfully",
"data": {
"id": "uuid",
"full_name": "Maria Fernandez",
"email": "[maria@example.com](mailto:maria@example.com)",
"role": "MANAGER",
"is_active": true
}
}

POST /auth/login

Input:

{
"email": "[maria@example.com](mailto:maria@example.com)",
"password": "Password123"
}

Output 200:

{
"success": true,
"message": "Login successful",
"data": {
"access_token": "jwt_token",
"token_type": "bearer",
"expires_in": 3600,
"user": {
"id": "uuid",
"full_name": "Maria Fernandez",
"email": "[maria@example.com](mailto:maria@example.com)",
"role": "MANAGER"
}
}
}

GET /auth/me

Headers:

Authorization: Bearer token

Output 200:

{
"success": true,
"message": "Current user retrieved successfully",
"data": {
"id": "uuid",
"full_name": "Maria Fernandez",
"email": "[maria@example.com](mailto:maria@example.com)",
"role": "MANAGER",
"is_active": true
}
}

---

## 10.2 USERS

GET /users

Query params:

* search
* role
* is_active
* page
* page_size

Reglas:

* Solo ADMIN puede listar todos los usuarios.
* No devolver password_hash.

Output:

{
"success": true,
"message": "Users retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"full_name": "Manager Demo 01",
"email": "[manager1@Resoruse Hub.com](mailto:manager1@Resoruse Hub.com)",
"role": "MANAGER",
"is_active": true
}
],
"total": 1,
"page": 1,
"page_size": 10
}
}

POST /users

Input:

{
"full_name": "Analista Demo 01",
"email": "[analyst1@Resoruse Hub.com](mailto:analyst1@Resoruse Hub.com)",
"password": "Analyst123",
"role": "ANALYST",
"is_active": true
}

Output 201:

{
"success": true,
"message": "User created successfully",
"data": {
"id": "uuid",
"full_name": "Analista Demo 01",
"email": "[analyst1@Resoruse Hub.com](mailto:analyst1@Resoruse Hub.com)",
"role": "ANALYST",
"is_active": true
}
}

---

## 10.3 PROVIDERS

GET /providers

Query params:

* search
* is_active
* page
* page_size

Output:

{
"success": true,
"message": "Providers retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"name": "Proveedor Demo SAP",
"ruc": null,
"contact_name": null,
"contact_email": null,
"is_active": true,
"created_at": "2026-06-10T10:00:00"
}
],
"total": 1,
"page": 1,
"page_size": 10
}
}

POST /providers

Input:

{
"name": "Proveedor Demo SAP",
"ruc": null,
"contact_name": null,
"contact_email": null
}

Validaciones:

* name obligatorio.
* name debe tener al menos 2 caracteres.
* name debe ser único usando normalización.
* contact_email debe tener formato email si se envía.
* ruc opcional.
* No asumir que todos los proveedores tendrán RUC o contacto.

Output 201:

{
"success": true,
"message": "Provider created successfully",
"data": {
"id": "uuid",
"name": "Proveedor Demo SAP",
"ruc": null,
"contact_name": null,
"contact_email": null,
"is_active": true
}
}

PUT /providers/{provider_id}

Input:

{
"name": "Proveedor Demo SAP Actualizado",
"ruc": null,
"contact_name": null,
"contact_email": null,
"is_active": true
}

Output:

{
"success": true,
"message": "Provider updated successfully",
"data": {
"id": "uuid",
"name": "Proveedor Demo SAP Actualizado",
"is_active": true
}
}

---

## 10.4 INITIATIVES

GET /initiatives

Query params:

* search
* responsible_manager_id
* is_active
* page
* page_size

POST /initiatives

Input:

{
"name": "Implementación SAP",
"description": "Proyecto de implementación SAP",
"responsible_manager_id": "uuid",
"budget_usd": 50000.00
}

Validaciones:

* name obligatorio y único.
* budget_usd mayor o igual a 0 si se envía.
* responsible_manager_id debe existir si se envía.

Output 201:

{
"success": true,
"message": "Initiative created successfully",
"data": {
"id": "uuid",
"name": "Implementación SAP",
"description": "Proyecto de implementación SAP",
"responsible_manager_id": "uuid",
"budget_usd": 50000.00,
"is_active": true
}
}

---

## 10.5 EXTERNAL RESOURCES

GET /external-resources

Query params:

* search
* technical_profile
* is_active
* page
* page_size

Output:

{
"success": true,
"message": "External resources retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"consultant_name": "Consultor Demo 01",
"technical_profile": "ABAP",
"document_number": null,
"is_active": true
}
],
"total": 1,
"page": 1,
"page_size": 10
}
}

POST /external-resources

Input:

{
"consultant_name": "Consultor Demo 01",
"technical_profile": "ABAP",
"document_number": null
}

Validaciones:

* consultant_name obligatorio.
* technical_profile obligatorio.
* technical_profile no debe confundirse con proveedor.

Output 201:

{
"success": true,
"message": "External resource created successfully",
"data": {
"id": "uuid",
"consultant_name": "Consultor Demo 01",
"technical_profile": "ABAP",
"document_number": null,
"is_active": true
}
}

---

## 10.6 ASSIGNMENTS

GET /assignments

Query params:

* manager_id
* provider_id
* initiative_id
* status
* alert
* search
* page
* page_size

Reglas:

* Si el usuario autenticado es MANAGER, ignorar manager_id externo y filtrar por su propio user_id.
* Si el usuario autenticado es ADMIN, puede filtrar por cualquier manager.
* Si el usuario autenticado es ANALYST, mostrar donde analyst_responsible_id sea su user_id.

Output:

{
"success": true,
"message": "Assignments retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"consultant_name": "Consultor Demo 01",
"technical_profile": "ABAP",
"provider_name": "Proveedor Demo SAP",
"main_initiative_name": "Implementación SAP",
"manager_name": "Manager Demo 01",
"analyst_responsible_name": "Analista Demo 01",
"start_date": "2026-06-01",
"end_date": "2026-08-31",
"duration_months": 3,
"monthly_cost": 2500.00,
"currency": "USD",
"exchange_rate": null,
"monthly_cost_usd": 2500.00,
"total_cost_usd": 7500.00,
"status": "ACTIVE",
"days_to_end": 25,
"expiration_alert": "AMBER",
"purchase_orders_count": 3
}
],
"total": 1,
"page": 1,
"page_size": 10
}
}

POST /assignments

Input:

{
"resource_id": "uuid",
"provider_id": "uuid",
"main_initiative_id": "uuid",
"manager_id": "uuid",
"analyst_responsible_id": "uuid",
"start_date": "2026-06-01",
"end_date": "2026-08-31",
"duration_months": 3,
"monthly_cost": 2500.00,
"currency": "USD",
"exchange_rate": null,
"comments": "Asignación demo para perfil ABAP",
"initiatives": [
{
"initiative_id": "uuid",
"allocation_percentage": 100,
"is_primary": true,
"is_funding_source": true
}
]
}

Validaciones:

* resource_id debe existir.
* provider_id debe existir.
* main_initiative_id debe existir.
* manager_id debe existir y debe tener rol MANAGER o ADMIN.
* analyst_responsible_id debe existir si se envía.
* start_date obligatorio.
* end_date obligatorio.
* end_date >= start_date.
* duration_months > 0.
* monthly_cost >= 0.
* currency debe ser USD o PEN.
* Si currency = PEN, exchange_rate obligatorio y mayor a 0.
* La suma de allocation_percentage no debe exceder 100.
* Debe existir solo una iniciativa principal.
* Debe existir solo una fuente de fondeo.
* Calcular monthly_cost_usd y total_cost_usd automáticamente.

Output 201:

{
"success": true,
"message": "Assignment created successfully",
"data": {
"id": "uuid",
"resource_id": "uuid",
"monthly_cost_usd": 2500.00,
"total_cost_usd": 7500.00,
"status": "ACTIVE"
}
}

POST /assignments/{assignment_id}/generate-monthly-purchase-orders

Descripción:

Genera automáticamente una OC pendiente por cada mes dentro del periodo de asignación.

Input:

{
"overwrite_existing": false
}

Reglas:

* Si overwrite_existing = false, no duplicar OCs existentes.
* Si la asignación es de 3 meses, generar 3 OCs.
* Cada OC se crea con status PENDING.
* amount debe ser igual al monthly_cost de la asignación.
* currency debe ser igual a la moneda de la asignación.
* exchange_rate debe copiarse de la asignación.
* amount_usd debe calcularse.
* period_month debe ser el primer día de cada mes.
* provider_id debe copiarse desde la asignación.

Output 201:

{
"success": true,
"message": "Monthly purchase orders generated successfully",
"data": {
"assignment_id": "uuid",
"generated_count": 3,
"skipped_count": 0,
"items": [
{
"id": "uuid",
"period_month": "2026-06-01",
"status": "PENDING",
"amount_usd": 2500.00
},
{
"id": "uuid",
"period_month": "2026-07-01",
"status": "PENDING",
"amount_usd": 2500.00
},
{
"id": "uuid",
"period_month": "2026-08-01",
"status": "PENDING",
"amount_usd": 2500.00
}
]
}
}

---

## 10.7 PURCHASE ORDERS

GET /purchase-orders

Query params:

* assignment_id
* provider_id
* status
* period_from
* period_to
* page
* page_size

Output:

{
"success": true,
"message": "Purchase orders retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"assignment_id": "uuid",
"consultant_name": "Consultor Demo 01",
"provider_name": "Proveedor Demo SAP",
"period_month": "2026-06-01",
"po_number": "OC-2026-001",
"status": "APPROVED",
"amount": 2500.00,
"currency": "USD",
"exchange_rate": null,
"amount_usd": 2500.00,
"comments": "OC aprobada"
}
],
"total": 1,
"page": 1,
"page_size": 10
}
}

POST /purchase-orders

Input:

{
"assignment_id": "uuid",
"period_month": "2026-06-01",
"po_number": "OC-2026-001",
"status": "PENDING",
"amount": 2500.00,
"currency": "USD",
"exchange_rate": null,
"comments": "OC de junio"
}

Validaciones:

* assignment_id debe existir.
* period_month debe ser el primer día del mes.
* No debe existir otra OC para el mismo assignment_id y period_month.
* period_month debe estar dentro del rango de la asignación.
* amount >= 0.
* currency debe ser USD o PEN.
* Si currency = PEN, exchange_rate obligatorio.
* provider_id se obtiene desde la asignación, no desde el input.
* amount_usd se calcula automáticamente.

Output 201:

{
"success": true,
"message": "Purchase order created successfully",
"data": {
"id": "uuid",
"assignment_id": "uuid",
"period_month": "2026-06-01",
"po_number": "OC-2026-001",
"status": "PENDING",
"amount_usd": 2500.00
}
}

PUT /purchase-orders/{purchase_order_id}

Input:

{
"po_number": "OC-2026-001",
"status": "APPROVED",
"amount": 2500.00,
"currency": "USD",
"exchange_rate": null,
"comments": "OC aprobada en Coupa"
}

Output:

{
"success": true,
"message": "Purchase order updated successfully",
"data": {
"id": "uuid",
"po_number": "OC-2026-001",
"status": "APPROVED",
"amount_usd": 2500.00
}
}

---

## 10.8 DASHBOARD

GET /dashboard/summary

Reglas:

* ADMIN ve todo.
* MANAGER ve solo su información.
* ANALYST ve solo recursos asociados a él.

Output:

{
"success": true,
"message": "Dashboard summary retrieved successfully",
"data": {
"active_assignments": 10,
"expiring_soon": 3,
"expired": 1,
"total_monthly_cost_usd": 25000.00,
"total_committed_cost_usd": 180000.00,
"purchase_orders": {
"total": 30,
"pending": 8,
"coupa_generated": 5,
"sent": 4,
"approved": 10,
"closed": 3
},
"expiration_alerts": {
"green": 6,
"amber": 3,
"red": 1
}
}
}

GET /dashboard/expiring-resources

Output:

{
"success": true,
"message": "Expiring resources retrieved successfully",
"data": [
{
"assignment_id": "uuid",
"consultant_name": "Consultor Demo 01",
"technical_profile": "ABAP",
"provider_name": "Proveedor Demo SAP",
"main_initiative_name": "Implementación SAP",
"end_date": "2026-06-30",
"days_to_end": 10,
"expiration_alert": "RED"
}
]
}

============================================================
11. MÓDULO DE IMPORTACIÓN HISTÓRICA DESDE EXCEL
===============================================

Crear un módulo para importar data histórica desde un archivo Excel.

Endpoint:

POST /imports/historical-excel

Content-Type:

multipart/form-data

Input:

* file: archivo .xlsx obligatorio
* default_manager_id: UUID opcional
* default_exchange_rate: decimal opcional
* auto_generate_purchase_orders: boolean, default true

Validaciones del archivo:

* Solo aceptar .xlsx.
* Validar que existan las columnas requeridas.
* Validar que cada fila tenga datos mínimos.
* Registrar errores por fila sin detener toda la carga.
* Crear import_batch.
* Crear import_batch_errors por cada fila inválida.

Columnas esperadas:

* Proyecto
* Consultor
* Analista responsable
* Proveedor
* Perfil
* Costo Mensual [USD]
* Costo Mensual [PEN]
* Duración
* Costo Total [USD]
* Costo Total [PEN]
* Inicio
* Fin
* Comentarios
* Mes1
* Mes2
* Mes3
* Mes4
* Mes5
* Mes6
* Mes7
* Mes8

Mapeo:

* Proyecto -> initiatives.name
* Consultor -> external_resources.consultant_name
* Analista responsable -> app_users.full_name o referencia si existe
* Proveedor -> providers.name
* Perfil -> external_resources.technical_profile
* Costo Mensual [USD] -> monthly_cost con currency USD
* Costo Mensual [PEN] -> monthly_cost con currency PEN
* Duración -> duration_months
* Inicio -> start_date
* Fin -> end_date
* Comentarios -> resource_assignments.comments
* Mes1..Mes8 -> purchase_orders.status por cada mes

Reglas de importación:

* Si una fila es válida:

  * Crear o reutilizar provider por nombre.
  * Crear o reutilizar initiative por nombre de Proyecto.
  * Crear o reutilizar external_resource por nombre de Consultor.
  * Crear resource_assignment.
  * Crear purchase_orders mensuales según columnas Mes1, Mes2, Mes3, etc. o según duración.

Reglas para proveedor:

* Si el proveedor viene vacío, registrar error de fila.
* Si el proveedor existe, reutilizarlo.
* Si el proveedor no existe, crearlo automáticamente.
* No reemplazar el proveedor por un valor fijo.
* No mapear proveedores a empresas inventadas.
* No usar catálogos quemados en código.
* El proveedor debe venir del Excel o de creación manual por API.

Reglas de moneda:

* Si Costo Mensual [USD] tiene valor mayor a 0, usar currency USD.
* Si Costo Mensual [USD] está vacío o es 0 y Costo Mensual [PEN] tiene valor, usar currency PEN.
* Si currency = PEN, usar default_exchange_rate si no hay tipo de cambio en el archivo.
* Si no hay tipo de cambio para PEN, registrar error de fila.

Mapeo de estados de OC desde Excel:

* "Pendiente" -> PENDING
* "Coupa generado" -> COUPA_GENERATED
* "OC enviada" -> SENT
* "Enviada" -> SENT
* "Aprobada" -> APPROVED
* "Cerrada" -> CLOSED
* vacío -> PENDING

Si auto_generate_purchase_orders = true y no hay estados mensuales claros, generar OCs PENDING según duración.

Output 200:

{
"success": true,
"message": "Historical Excel import completed",
"data": {
"batch_id": "uuid",
"file_name": "historico.xlsx",
"status": "COMPLETED_WITH_ERRORS",
"total_rows": 25,
"successful_rows": 22,
"failed_rows": 3,
"created": {
"providers": 4,
"initiatives": 5,
"external_resources": 10,
"assignments": 22,
"purchase_orders": 66
},
"errors": [
{
"row_number": 8,
"column_name": "Costo Mensual [PEN]",
"error_message": "Exchange rate is required for PEN currency"
}
]
}
}

GET /imports

Output:

{
"success": true,
"message": "Import batches retrieved successfully",
"data": {
"items": [
{
"id": "uuid",
"file_name": "historico.xlsx",
"imported_by": "uuid",
"total_rows": 25,
"successful_rows": 22,
"failed_rows": 3,
"status": "COMPLETED_WITH_ERRORS",
"created_at": "2026-06-10T10:00:00"
}
],
"total": 1
}
}

GET /imports/{batch_id}/errors

Output:

{
"success": true,
"message": "Import errors retrieved successfully",
"data": [
{
"row_number": 8,
"column_name": "Costo Mensual [PEN]",
"error_message": "Exchange rate is required for PEN currency",
"raw_data": {}
}
]
}

============================================================
12. VALIDACIONES GENERALES
==========================

Implementar validaciones con Pydantic y también con lógica de negocio en services.

Validaciones obligatorias:

* UUID válido.
* Fechas válidas.
* Montos no negativos.
* Emails válidos.
* Monedas válidas.
* Estados válidos.
* Roles válidos.
* No duplicar proveedores por nombre normalizado.
* No duplicar iniciativas por nombre.
* No duplicar OC por asignación y mes.
* No permitir OC fuera del rango de asignación.
* No permitir acceso a datos de otro manager si el usuario no es ADMIN.
* No retornar password_hash.
* No permitir crear asignaciones sin recurso, proveedor, iniciativa y manager existentes.
* No permitir que la suma de asignaciones parciales supere 100%.
* No permitir más de una iniciativa principal por asignación.
* No permitir más de una fuente de fondeo por asignación.

============================================================
13. SEMÁFORO DE VENCIMIENTO
===========================

Calcular days_to_end como:

end_date - current_date

Reglas:

* GREEN: más de 30 días.
* AMBER: entre 15 y 30 días.
* RED: menos de 15 días o vencido.

El dashboard y los endpoints de assignments deben devolver expiration_alert.

============================================================
14. SEED DATA PARA DEMO
=======================

Crear script de seed con datos ficticios.

Usuarios:

* [admin@Resoruse Hub.com](mailto:admin@Resoruse Hub.com) / Admin123 / ADMIN
* [manager1@Resoruse Hub.com](mailto:manager1@Resoruse Hub.com) / Manager123 / MANAGER
* [manager2@Resoruse Hub.com](mailto:manager2@Resoruse Hub.com) / Manager123 / MANAGER
* [manager3@Resoruse Hub.com](mailto:manager3@Resoruse Hub.com) / Manager123 / MANAGER
* [analyst1@Resoruse Hub.com](mailto:analyst1@Resoruse Hub.com) / Analyst123 / ANALYST
* [analyst2@Resoruse Hub.com](mailto:analyst2@Resoruse Hub.com) / Analyst123 / ANALYST

Proveedores demo:

* Proveedor Demo SAP
* Proveedor Demo Workato
* Proveedor Demo Full Stack
* Proveedor Demo BW
* Proveedor Demo Data Analytics

No usar empresas reales no indicadas.

Iniciativas:

* Implementación SAP
* Integraciones Workato
* Finance Platform
* Migración BW
* Automatización Coupa

Recursos externos:

Crear al menos 10 consultores ficticios con perfiles:

* ABAP
* FI
* Full Stack
* Workato
* BW
* QA
* Data
* Integraciones SAP
* Backend Python
* Frontend Angular

Asignaciones:

* Crear asignaciones de 1, 3, 6 y 8 meses.
* Algunas próximas a vencer en menos de 15 días.
* Algunas entre 15 y 30 días.
* Algunas con más de 30 días.
* Algunas en USD.
* Algunas en PEN con tipo de cambio.

OCs:

* Generar OCs mensuales para cada asignación.
* Usar estados variados:

  * PENDING
  * COUPA_GENERATED
  * SENT
  * APPROVED
  * CLOSED

============================================================
15. DOCUMENTACIÓN .MD OBLIGATORIA
=================================

Crear archivo:

BACKEND_DOCUMENTATION.md

Debe contener:

1. Nombre del proyecto

Resoruse Hub Backend

2. Descripción

API REST para gestionar recursos externos, asignaciones, proveedores, iniciativas, OCs mensuales, dashboard e importación histórica desde Excel.

3. Stack utilizado

FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT, Pydantic, openpyxl.

4. Arquitectura de carpetas

Explicar brevemente cada carpeta.

5. Modelo de datos

Describir cada tabla y sus relaciones.

6. Reglas de negocio

Incluir:

* Cálculo de costos en USD.
* Generación mensual de OCs.
* Semáforo de vencimiento.
* Filtro por manager.
* Importación histórica desde Excel.
* Tratamiento flexible de proveedores.
* Uso de perfiles técnicos.

7. Tratamiento de proveedores

Explicar:

* Los proveedores son configurables.
* No existe catálogo cerrado de proveedores.
* Los proveedores pueden venir desde el Excel histórico.
* Los proveedores pueden crearse manualmente por API.
* El sistema evita duplicados normalizando nombres.
* Los nombres usados en seed son ficticios y solo para demo.
* No se usan empresas reales no proporcionadas por el usuario.

8. Perfiles técnicos

Explicar:

* Los perfiles técnicos se guardan en external_resources.technical_profile.
* Para la demo se usan perfiles alineados al reto:
  ABAP, FI, Full Stack, Workato, BW, QA, Data, Integraciones SAP, Backend Python, Frontend Angular.
* El perfil técnico no debe confundirse con el proveedor.
* El proveedor es la empresa que suministra al recurso.
* El perfil técnico describe la especialidad del consultor.

9. Endpoints

Documentar cada endpoint con:

* Método
* Ruta
* Descripción
* Input esperado
* Output esperado
* Reglas de validación

10. Seguridad

Explicar:

* Login
* JWT
* Bearer token
* Roles
* Restricción por manager

11. Importación Excel

Explicar:

* Columnas esperadas.
* Reglas de mapeo.
* Manejo de errores por fila.
* Resultado de importación.
* Creación/reutilización de proveedores.

12. Variables de entorno

Listar las variables necesarias.

13. Cómo ejecutar localmente

Incluir comandos para:

* Crear entorno virtual.
* Instalar dependencias.
* Configurar .env.
* Ejecutar migraciones.
* Cargar seed data.
* Levantar servidor.

14. Datos seed

Explicar cómo cargar datos iniciales.

15. Decisiones técnicas

Explicar por qué se usó:

* FastAPI
* PostgreSQL
* JWT
* SQLAlchemy
* Alembic
* openpyxl

16. Limitaciones actuales

* No hay frontend todavía.
* No hay integración real con Coupa.
* No hay IA todavía.
* No hay envío de notificaciones.

17. Próximos pasos

* Conectar frontend Angular.
* Agregar Workato GO.
* Agregar reportes ejecutivos.
* Agregar pruebas automatizadas completas.

También actualizar README.md con una versión resumida:

* Descripción.
* Stack.
* Instalación.
* Ejecución.
* Endpoints principales.
* Autenticación.
* Importación Excel.
* Link o referencia a BACKEND_DOCUMENTATION.md.

============================================================
16. CRITERIOS DE CALIDAD ANTES DE FINALIZAR
===========================================

Antes de dar por terminado el backend, validar:

* El proyecto levanta con uvicorn.
* Swagger carga correctamente.
* Login funciona.
* El token se genera correctamente.
* Los endpoints protegidos rechazan requests sin token.
* Los endpoints protegidos aceptan requests con token válido.
* No se devuelve password_hash.
* CRUDs principales funcionan.
* Filtro por manager funciona.
* Cálculos de USD funcionan.
* Generación mensual de OCs funciona.
* Importación desde Excel funciona con errores controlados por fila.
* Alembic genera y aplica migraciones.
* README.md existe y está actualizado.
* BACKEND_DOCUMENTATION.md existe y explica todo lo creado.
* No hay imports rotos.
* No hay variables sin usar importantes.
* No hay endpoints incompletos.
* No hay TODOs pendientes.
* No se usan proveedores reales no proporcionados.
* Los proveedores demo son genéricos.
* El código está limpio, ordenado y mantenible.

============================================================
17. RESULTADO ESPERADO
======================

Resultado esperado:

Un backend profesional, seguro, validado, documentado y listo para conectarse después con un frontend Angular.

Debe incluir:

* Autenticación JWT.
* CRUD de usuarios.
* CRUD de proveedores configurables.
* CRUD de iniciativas.
* CRUD de recursos externos.
* CRUD de asignaciones.
* Generación automática de OCs mensuales.
* CRUD de órdenes de compra.
* Dashboard resumen.
* Importador histórico desde Excel.
* Seed data ficticia.
* README.md.
* BACKEND_DOCUMENTATION.md.
* Estructura profesional sin errores.
