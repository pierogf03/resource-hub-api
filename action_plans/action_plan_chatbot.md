PLAN FINAL BACKEND — RESOURCE HUB AI ASSISTANT POR API

Objetivo:
Implementar en el backend FastAPI de Resource Hub una integración final de chat con Workato/Genie usando un endpoint API propio. El frontend Angular enviará mensajes al backend, el backend llamará a un endpoint API de Workato, Workato ejecutará la lógica del Genie y sus skills, y el backend devolverá la respuesta al frontend.

Este enfoque reemplaza la integración por Headless API. No usar el término temporal. Esta será la arquitectura final del chat IA para Resource Hub.

Nombre del sistema:
Resource Hub

Nombre del asistente:
Resource Hub Assistant

Objetivo funcional del asistente:
Permitir que un usuario consulte en lenguaje natural el estado de recursos externos, asignaciones, vencimientos, OCs mensuales, presupuesto e importaciones históricas. Además, debe poder sugerir acciones controladas como generar OCs mensuales o actualizar estados de OCs, siempre con confirmación del usuario antes de ejecutar cambios.

============================================================

1. ARQUITECTURA FINAL
   ============================================================

Arquitectura:

Angular Resource Hub
↓
POST /ai/chat/messages
↓
FastAPI Resource Hub
↓
Workato API Endpoint / Recipe del Genie
↓
Skills Workato
↓
FastAPI /internal/workato
↓
PostgreSQL Resource Hub
↓
Respuesta del Genie
↓
FastAPI
↓
Angular Chat

Reglas:

* Angular nunca llama directamente a Workato.
* Angular nunca guarda API keys de Workato.
* FastAPI es el único componente que conoce la URL y API key de Workato.
* Workato llama a Resource Hub únicamente por endpoints internos protegidos.
* El backend sigue siendo la fuente de verdad de permisos, reglas de negocio y datos.
* El chat IA es una capa conversacional, no reemplaza los módulos core del sistema.

============================================================
2. CUMPLIMIENTO DEL CHALLENGE
=============================

El asistente debe apoyar los módulos solicitados por el challenge:

Core:

* Registro y consulta de recursos externos.
* Alertas de vencimiento con semáforo.
* Control de órdenes de compra mensuales.
* Visibilidad de costos en USD.
* Separación de información por manager.

Bonus:

* IA integrada mediante Workato/Genie.

El asistente debe responder preguntas como:

* Dame un resumen del área.
* ¿Qué recursos están por vencer?
* ¿Qué recursos están en rojo?
* ¿Cuántas OCs están pendientes?
* Muéstrame las OCs de este mes.
* ¿Cuál es el presupuesto comprometido?
* ¿Cómo salió la última importación?
* Genera las OCs mensuales de una asignación.
* Marca una OC como aprobada.

============================================================
3. MANTENER MÓDULOS EXISTENTES
==============================

No romper ni eliminar:

* Auth JWT
* Usuarios
* Proveedores
* Iniciativas
* Recursos externos
* Asignaciones
* Órdenes de compra
* Dashboard
* Importación histórica Excel
* Endpoints /internal/workato
* Tabla ai_chat_audit_logs
* Auditoría IA
* README.md
* BACKEND_DOCUMENTATION.md

No usar:

* ResourcePulse
* Resoruse Hub

Usar siempre:

* Resource Hub

============================================================
4. VARIABLES DE ENTORNO
=======================

Agregar o ajustar en .env.example:

WORKATO_AI_CHAT_URL=https://www.workato.com/api/resource-hub-assistant/message
WORKATO_AI_CHAT_API_KEY=change_me
WORKATO_INTERNAL_API_KEY=change_me_internal_key
AI_CHAT_ENABLED=true
AI_CHAT_AUDIT_ENABLED=true
AI_CHAT_TIMEOUT_SECONDS=60
AI_CHAT_MAX_MESSAGE_LENGTH=4000

Descripción:

WORKATO_AI_CHAT_URL:
Endpoint API de Workato que recibirá el mensaje del usuario y devolverá la respuesta del Genie.

WORKATO_AI_CHAT_API_KEY:
API key usada por FastAPI para llamar al endpoint de Workato. Nunca exponer en frontend.

WORKATO_INTERNAL_API_KEY:
API key que Workato usa para llamar endpoints internos de Resource Hub.

AI_CHAT_ENABLED:
Activa o desactiva el chat IA.

AI_CHAT_AUDIT_ENABLED:
Activa auditoría de mensajes, respuestas y acciones.

AI_CHAT_TIMEOUT_SECONDS:
Timeout máximo para la llamada a Workato.

AI_CHAT_MAX_MESSAGE_LENGTH:
Longitud máxima del mensaje del usuario.

============================================================
5. ARCHIVOS A CREAR O AJUSTAR
=============================

Crear:

app/routers/ai_chat_api.py
app/services/ai_chat_api_service.py
app/schemas/ai_chat_api_schema.py

Ajustar:

app/core/config.py
app/main.py
app/models/ai_chat_audit.py
app/repositories/ai_chat_audit_repository.py
app/routers/workato_internal.py
app/services/dashboard_service.py
app/services/assignment_service.py
app/services/purchase_order_service.py
README.md
BACKEND_DOCUMENTATION.md

============================================================
6. ENDPOINT PRINCIPAL DEL CHAT
==============================

Crear endpoint:

POST /ai/chat/messages

Descripción:
Recibe un mensaje desde el frontend, lo envía al endpoint API de Workato/Genie y devuelve la respuesta del asistente.

Autenticación:
Requiere JWT Bearer.

Input:

{
"message": "¿Qué recursos están por vencer?",
"conversation_id": "optional-string",
"metadata": {
"screen": "dashboard",
"source": "resource-hub-web"
}
}

Validaciones:

* message obligatorio.
* message mínimo 1 carácter.
* message máximo definido por AI_CHAT_MAX_MESSAGE_LENGTH.
* conversation_id opcional.
* metadata opcional.
* Usuario debe estar autenticado.
* AI_CHAT_ENABLED debe ser true.

Output exitoso:

{
"success": true,
"message": "Assistant response retrieved successfully",
"data": {
"conversation_id": "conv-uuid-or-workato-id",
"reply": "Actualmente tienes 10 asignaciones activas, 3 recursos por vencer y 8 OCs pendientes.",
"intent": "dashboard_summary",
"used_skills": [
"get_dashboard_summary"
],
"suggested_questions": [
"¿Qué recursos están en rojo?",
"¿Qué OCs están pendientes este mes?"
],
"requires_confirmation": false,
"pending_action": null,
"created_at": "2026-06-14T10:00:00Z"
}
}

Output con acción pendiente:

{
"success": true,
"message": "Assistant response retrieved successfully",
"data": {
"conversation_id": "conv-uuid-or-workato-id",
"reply": "Encontré la asignación de Consultor Demo ABAP. Para generar sus OCs mensuales necesito tu confirmación.",
"intent": "generate_monthly_purchase_orders",
"used_skills": [
"search_assignments"
],
"suggested_questions": [],
"requires_confirmation": true,
"pending_action": {
"action_id": "action-uuid",
"action_type": "generate_monthly_purchase_orders",
"summary": "Generar OCs mensuales para la asignación Consultor Demo ABAP.",
"payload": {
"assignment_id": "uuid",
"overwrite_existing": false
}
},
"created_at": "2026-06-14T10:00:00Z"
}
}

Output error:

{
"success": false,
"message": "The assistant is not available at this moment",
"errors": [
{
"field": "assistant",
"message": "Timeout calling Workato AI chat endpoint"
}
]
}

============================================================
7. ENDPOINT PARA CONFIRMAR ACCIONES
===================================

Crear endpoint:

POST /ai/chat/actions/confirm

Descripción:
Confirma o rechaza una acción pendiente sugerida por el asistente.

Autenticación:
Requiere JWT Bearer.

Input:

{
"conversation_id": "conv-uuid-or-workato-id",
"action_id": "action-uuid",
"approved": true,
"rejection_reason": null
}

Validaciones:

* conversation_id obligatorio.
* action_id obligatorio.
* approved obligatorio.
* La acción pendiente debe pertenecer al usuario autenticado.
* No ejecutar acciones si approved = false.
* Validar permisos antes de ejecutar cualquier acción real.

Output aprobado:

{
"success": true,
"message": "Action confirmation processed successfully",
"data": {
"conversation_id": "conv-uuid-or-workato-id",
"action_id": "action-uuid",
"status": "APPROVED",
"reply": "Listo. Se generaron 3 OCs mensuales para la asignación seleccionada.",
"result": {
"generated_count": 3,
"skipped_count": 0
}
}
}

Output rechazado:

{
"success": true,
"message": "Action rejected successfully",
"data": {
"conversation_id": "conv-uuid-or-workato-id",
"action_id": "action-uuid",
"status": "REJECTED",
"reply": "Acción cancelada. No se realizó ningún cambio."
}
}

============================================================
8. PAYLOAD QUE FASTAPI ENVÍA A WORKATO
======================================

Cuando el frontend llame POST /ai/chat/messages, FastAPI debe llamar:

POST {{WORKATO_AI_CHAT_URL}}

Headers:

Authorization: Bearer {{WORKATO_AI_CHAT_API_KEY}}
Content-Type: application/json
Accept: application/json

Body:

{
"message": "¿Qué recursos están por vencer?",
"conversation_id": "optional-string",
"user": {
"id": "uuid",
"full_name": "Admin Demo",
"email": "[admin@resourcehub.com](mailto:admin@resourcehub.com)",
"role": "ADMIN"
},
"resource_hub_context": {
"app_name": "Resource Hub",
"source": "web",
"permissions_mode": "backend_enforced",
"allowed_capabilities": [
"dashboard_summary",
"expiring_resources",
"assignments_search",
"purchase_orders_search",
"budget_summary",
"import_status",
"confirmed_actions"
]
},
"metadata": {
"screen": "dashboard",
"timestamp": "2026-06-14T10:00:00Z"
}
}

Reglas:

* No enviar password_hash.
* No enviar JWT del usuario.
* No enviar datos sensibles innecesarios.
* No confiar en Workato para permisos.
* Workato puede interpretar intención y orquestar skills.
* Resource Hub valida toda acción real.

============================================================
9. RESPUESTA ESPERADA DESDE WORKATO
===================================

Workato debe devolver siempre JSON con esta forma:

{
"conversation_id": "conv-uuid-or-workato-id",
"reply": "Texto final que debe mostrarse al usuario.",
"intent": "dashboard_summary",
"used_skills": [
"get_dashboard_summary"
],
"suggested_questions": [
"¿Qué recursos están en rojo?"
],
"requires_confirmation": false,
"pending_action": null
}

Si requiere confirmación:

{
"conversation_id": "conv-uuid-or-workato-id",
"reply": "Necesito tu confirmación para ejecutar esta acción.",
"intent": "generate_monthly_purchase_orders",
"used_skills": [
"search_assignments"
],
"requires_confirmation": true,
"pending_action": {
"action_id": "action-uuid",
"action_type": "generate_monthly_purchase_orders",
"summary": "Generar OCs mensuales para Consultor Demo ABAP.",
"payload": {
"assignment_id": "uuid",
"overwrite_existing": false
}
},
"suggested_questions": []
}

Si hay error controlado:

{
"conversation_id": "conv-uuid-or-workato-id",
"reply": "No pude obtener la información solicitada en este momento.",
"intent": "error",
"used_skills": [],
"requires_confirmation": false,
"pending_action": null,
"error": {
"code": "RESOURCE_HUB_API_ERROR",
"message": "Error calling Resource Hub internal endpoint"
}
}

============================================================
10. SERVICIO ai_chat_api_service.py
===================================

Crear clase:

AiChatApiService

Métodos:

send_message(
message: str,
conversation_id: str | None,
current_user: AppUser,
metadata: dict | None
)

confirm_action(
conversation_id: str,
action_id: str,
approved: bool,
rejection_reason: str | None,
current_user: AppUser
)

Responsabilidad de send_message:

1. Validar AI_CHAT_ENABLED.
2. Armar payload para Workato.
3. Llamar WORKATO_AI_CHAT_URL con httpx.
4. Manejar timeout.
5. Manejar 401, 403, 404, 500 desde Workato.
6. Normalizar respuesta.
7. Guardar auditoría.
8. Devolver respuesta al router.

Responsabilidad de confirm_action:

1. Buscar acción pendiente en auditoría o almacenamiento definido.
2. Validar que pertenezca al current_user.
3. Si approved = false, registrar rechazo y devolver respuesta.
4. Si approved = true, ejecutar acción real usando services internos.
5. Validar permisos del usuario antes de ejecutar.
6. Auditar resultado.
7. Devolver respuesta final al frontend.

Timeout:
Usar AI_CHAT_TIMEOUT_SECONDS.

Retries:
No aplicar retries automáticos para evitar duplicar acciones.

Logs:

* No loguear API keys.
* No loguear tokens.
* Loguear solo user_id, conversation_id, intent, used_skills y status.

============================================================
11. ACCIONES SOPORTADAS CON CONFIRMACIÓN
========================================

Soportar estas acciones:

1. generate_monthly_purchase_orders

Payload esperado:

{
"assignment_id": "uuid",
"overwrite_existing": false
}

Ejecución:
Usar assignment_service.generate_monthly_purchase_orders.

Validaciones:

* assignment_id existe.
* El usuario tiene permiso sobre la asignación.
* Si el usuario es MANAGER, la asignación debe pertenecerle.
* Si el usuario es ANALYST, validar política definida.
* No duplicar OCs si overwrite_existing = false.

2. update_purchase_order_status

Payload esperado:

{
"purchase_order_id": "uuid",
"po_number": "OC-2026-001",
"status": "APPROVED",
"comments": "Actualizado desde Resource Hub Assistant"
}

Ejecución:
Usar purchase_order_service.update_status.

Validaciones:

* purchase_order_id existe.
* El usuario tiene permiso sobre la OC.
* status debe ser válido.
* No permitir cambios no soportados.

============================================================
12. ENDPOINTS INTERNOS PARA WORKATO
===================================

Mantener y validar estos endpoints:

GET /internal/workato/dashboard-summary
GET /internal/workato/expiring-resources
GET /internal/workato/assignments
GET /internal/workato/purchase-orders
GET /internal/workato/budget-summary
GET /internal/workato/import-status
POST /internal/workato/assignments/{id}/generate-monthly-purchase-orders
PUT /internal/workato/purchase-orders/{id}/status

Todos deben requerir:

Authorization: Bearer {{WORKATO_INTERNAL_API_KEY}}
X-ResourceHub-User-Id: uuid

Reglas:

* No confiar en role enviado por Workato.
* Buscar usuario real en base de datos.
* Aplicar permisos por rol.
* Responder con formato claro.
* No devolver datos fuera del alcance del usuario.

============================================================
13. SKILLS QUE WORKATO DEBE USAR
================================

El endpoint API de Workato debe poder orquestar estas skills:

Skills de consulta:

* get_dashboard_summary
* get_expiring_resources
* search_assignments
* get_purchase_orders_status
* get_budget_summary
* get_import_status

Skills de acción, siempre con confirmación:

* generate_monthly_purchase_orders
* update_purchase_order_status

Regla:
Las skills de acción no deben ejecutar cambios directamente desde el mensaje inicial. Workato debe devolver pending_action y Resource Hub debe pedir confirmación al usuario desde el frontend.

============================================================
14. AUDITORÍA
=============

Usar ai_chat_audit_logs.

Registrar:

CHAT_MESSAGE_SENT:

* user_id
* conversation_id
* message
* metadata

CHAT_MESSAGE_RESPONSE:

* conversation_id
* reply
* intent
* used_skills

CHAT_MESSAGE_FAILED:

* error_message
* status FAILED

CHAT_ACTION_PENDING:

* action_id
* action_type
* payload
* status PENDING_APPROVAL

CHAT_ACTION_APPROVED:

* action_id
* status APPROVED

CHAT_ACTION_REJECTED:

* action_id
* status REJECTED

CHAT_ACTION_EXECUTED:

* action_id
* result
* status SUCCESS

CHAT_ACTION_FAILED:

* action_id
* error_message
* status FAILED

============================================================
15. MANEJO DE ERRORES
=====================

Casos:

AI_CHAT_ENABLED = false:
Retornar 503:
"Resource Hub Assistant is disabled"

Timeout Workato:
Retornar 504:
"The assistant is taking too long to respond"

401/403 Workato:
Retornar 502:
"Assistant authentication failed"

500 Workato:
Retornar 502:
"Assistant service error"

Respuesta inválida:
Retornar 502:
"Invalid assistant response"

Error de acción:
Retornar 400 o 403 según corresponda.

============================================================
16. DOCUMENTACIÓN
=================

Actualizar README.md:

Agregar sección:
Resource Hub Assistant

Incluir:

* Arquitectura final por API.
* Endpoint POST /ai/chat/messages.
* Endpoint POST /ai/chat/actions/confirm.
* Variables de entorno.
* Contrato con Workato.
* Skills soportadas.
* Reglas de seguridad.
* Ejemplos de request/response.

Actualizar BACKEND_DOCUMENTATION.md:

Agregar:

* Integración final con Workato por API.
* Diferencia frente a Headless API.
* Payload enviado a Workato.
* Respuesta esperada de Workato.
* Auditoría.
* Confirmación de acciones.
* Reglas de permisos.

============================================================
17. PRUEBAS MANUALES
====================

Probar:

1. Login funciona.
2. POST /ai/chat/messages sin token devuelve 401.
3. POST /ai/chat/messages con token llama Workato.
4. El frontend recibe reply.
5. Pregunta "Dame un resumen del área" devuelve used_skills get_dashboard_summary.
6. Pregunta "Qué recursos están por vencer" devuelve datos de vencimiento.
7. Pregunta "Qué OCs están pendientes" devuelve OCs.
8. Pregunta "Cuál es el presupuesto comprometido" devuelve budget summary.
9. Pregunta "Cómo salió la última importación" devuelve import status.
10. Acción de generar OCs devuelve pending_action.
11. Confirmar acción ejecuta la generación de OCs.
12. Rechazar acción no ejecuta cambios.
13. Auditoría registra mensajes y acciones.
14. Usuario MANAGER no ve información de otros managers.
15. Usuario ADMIN ve todo.
16. README.md actualizado.
17. BACKEND_DOCUMENTATION.md actualizado.

============================================================
18. CRITERIOS DE ACEPTACIÓN
===========================

El backend queda completo cuando:

* Existe POST /ai/chat/messages.
* Existe POST /ai/chat/actions/confirm.
* Ambos endpoints requieren JWT.
* FastAPI llama al endpoint API de Workato.
* Workato puede llamar endpoints internos /internal/workato.
* El chat devuelve respuesta del asistente.
* Se soportan suggested_questions.
* Se soportan used_skills.
* Se soporta requires_confirmation.
* Las acciones se ejecutan solo después de confirmar.
* Se respetan permisos por rol.
* Se audita todo el flujo.
* No hay API keys expuestas.
* No hay referencias a ResourcePulse.
* No hay referencias a Resoruse Hub.
* Documentación actualizada.
* Código sin errores ni TODOs pendientes.

Resultado esperado:
Backend FastAPI de Resource Hub con integración final de Resource Hub Assistant vía API de Workato, cumpliendo el bonus de IA integrada del challenge y manteniendo la seguridad, trazabilidad y reglas del sistema.
