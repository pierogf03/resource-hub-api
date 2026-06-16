import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.user import AppUser
from app.repositories.ai_chat_audit_repository import AiChatAuditRepository
from app.schemas.ai_chat_api_schema import (
    ChatActionConfirmData,
    ChatMessageData,
    PendingAction,
    WorkatoChatRequest,
    WorkatoChatResponse,
    WorkatoResourceHubContext,
    WorkatoUserContext,
)
from app.schemas.assignment_schema import GeneratePurchaseOrdersRequest
from app.services.assignment_service import AssignmentService
from app.services.purchase_order_service import PurchaseOrderService
from app.utils.permission_utils import can_confirm_action

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_CAPABILITIES = [
    "get_dashboard_summary",
    "get_expiring_resources",
    "search_assignments",
    "get_purchase_orders_status",
    "get_budget_summary",
    "get_import_status",
    "confirmed_actions",
]


class AiChatApiService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AiChatAuditRepository(db)

    def _audit_enabled(self) -> bool:
        return settings.AI_CHAT_AUDIT_ENABLED

    def _create_audit(self, **kwargs: Any) -> None:
        if self._audit_enabled():
            self.audit_repo.create_log(**kwargs)

    def _build_workato_payload(
        self,
        message: str,
        conversation_id: str | None,
        current_user: AppUser,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        request_metadata = dict(metadata or {})
        request_metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload = WorkatoChatRequest(
            message=message,
            conversation_id=conversation_id,
            user=WorkatoUserContext(
                id=str(current_user.id),
                full_name=current_user.full_name,
                email=current_user.email,
                role=current_user.role,
            ),
            resource_hub_context=WorkatoResourceHubContext(allowed_capabilities=ALLOWED_CAPABILITIES),
            metadata=request_metadata,
        )
        return payload.model_dump(exclude_none=True)

    @staticmethod
    def _normalize_workato_response_body(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Workato response is not a JSON object")

        # Workato API Platform wraps the Genie payload, e.g.:
        # { "Response": 200, "response": { "conversation_id": "...", "reply": "..." } }
        if "conversation_id" not in data and "reply" not in data:
            for key in ("response", "body", "data", "result"):
                nested = data.get(key)
                if isinstance(nested, dict):
                    data = nested
                    break

        normalized = dict(data)
        if normalized.get("pending_action") in (None, "", {}, []):
            normalized["pending_action"] = None
        if normalized.get("error") in (None, "", {}, []):
            normalized["error"] = None
        return normalized

    def _call_workato(self, payload: dict[str, Any]) -> WorkatoChatResponse:
        if not settings.WORKATO_AI_CHAT_URL:
            raise AppException(
                "The assistant is not available at this moment",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                errors=[{"field": "assistant", "message": "Workato AI chat URL is not configured"}],
            )
        headers = {
            "API-TOKEN": f"{settings.WORKATO_AI_CHAT_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=settings.AI_CHAT_TIMEOUT_SECONDS) as client:
                response = client.post(settings.WORKATO_AI_CHAT_URL, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise AppException(
                "The assistant is taking too long to respond",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                errors=[{"field": "assistant", "message": "Timeout calling Workato AI chat endpoint"}],
            ) from exc
        except httpx.RequestError as exc:
            raise AppException(
                "The assistant is not available at this moment",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": str(exc)}],
            ) from exc

        if response.status_code in {401, 403}:
            raise AppException(
                "Assistant authentication failed",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": "Workato rejected API credentials"}],
            )
        if response.status_code >= 500:
            raise AppException(
                "Assistant service error",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": f"Workato returned status {response.status_code}"}],
            )
        if response.status_code >= 400:
            raise AppException(
                "The assistant is not available at this moment",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": f"Workato returned status {response.status_code}"}],
            )

        try:
            data = response.json()
            normalized = self._normalize_workato_response_body(data)
            workato_response = WorkatoChatResponse.model_validate(normalized)
        except Exception as exc:
            raise AppException(
                "Invalid assistant response",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": "Response could not be parsed"}],
            ) from exc

        if not workato_response.conversation_id or not workato_response.reply:
            raise AppException(
                "Invalid assistant response",
                status_code=status.HTTP_502_BAD_GATEWAY,
                errors=[{"field": "assistant", "message": "Missing conversation_id or reply"}],
            )
        return workato_response

    def send_message(
        self,
        message: str,
        conversation_id: str | None,
        current_user: AppUser,
        metadata: dict[str, Any] | None,
    ) -> ChatMessageData:
        if not settings.AI_CHAT_ENABLED:
            raise AppException("Resource Hub Assistant is disabled", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        self._create_audit(
            event_type="CHAT_MESSAGE_SENT",
            user_id=current_user.id,
            conversation_id=conversation_id,
            message=message,
            metadata=metadata,
        )

        payload = self._build_workato_payload(message, conversation_id, current_user, metadata)

        try:
            workato_response = self._call_workato(payload)
        except AppException as exc:
            self._create_audit(
                event_type="CHAT_MESSAGE_FAILED",
                user_id=current_user.id,
                conversation_id=conversation_id,
                error_message=exc.message,
                status="FAILED",
            )
            raise

        pending_action = None
        if workato_response.pending_action:
            pending_action = PendingAction(
                action_id=workato_response.pending_action.action_id,
                action_type=workato_response.pending_action.action_type,
                summary=workato_response.pending_action.summary,
                payload=workato_response.pending_action.payload,
            )

        self._create_audit(
            event_type="CHAT_MESSAGE_RESPONSE",
            user_id=current_user.id,
            conversation_id=workato_response.conversation_id,
            reply=workato_response.reply,
            intent=workato_response.intent,
            used_skills=workato_response.used_skills,
        )

        if workato_response.requires_confirmation and pending_action:
            self._create_audit(
                event_type="CHAT_ACTION_PENDING",
                user_id=current_user.id,
                conversation_id=workato_response.conversation_id,
                action_id=pending_action.action_id,
                action_type=pending_action.action_type,
                payload=pending_action.payload,
                status="PENDING_APPROVAL",
            )

        logger.info(
            "AI chat message processed user_id=%s conversation_id=%s intent=%s used_skills=%s",
            current_user.id,
            workato_response.conversation_id,
            workato_response.intent,
            workato_response.used_skills,
        )

        return ChatMessageData(
            conversation_id=workato_response.conversation_id,
            reply=workato_response.reply,
            intent=workato_response.intent,
            used_skills=workato_response.used_skills,
            suggested_questions=workato_response.suggested_questions,
            requires_confirmation=workato_response.requires_confirmation,
            pending_action=pending_action,
            created_at=datetime.now(timezone.utc),
        )

    def _execute_pending_action(self, action_type: str, payload: dict[str, Any], current_user: AppUser) -> dict[str, Any]:
        if action_type == "generate_monthly_purchase_orders":
            assignment_id = UUID(str(payload["assignment_id"]))
            overwrite_existing = bool(payload.get("overwrite_existing", False))
            result = AssignmentService(self.db).generate_monthly_purchase_orders(
                assignment_id,
                GeneratePurchaseOrdersRequest(overwrite_existing=overwrite_existing),
                current_user,
            )
            return {
                "generated_count": result.generated_count,
                "skipped_count": result.skipped_count,
            }

        if action_type == "update_purchase_order_status":
            purchase_order_id = UUID(str(payload["purchase_order_id"]))
            status_value = str(payload["status"])
            comments = payload.get("comments")
            po_number = payload.get("po_number")
            PurchaseOrderService(self.db).update_status(
                purchase_order_id,
                status_value,
                comments,
                current_user,
                po_number=po_number,
            )
            return {"purchase_order_id": str(purchase_order_id), "status": status_value}

        raise AppException(f"Unsupported action type: {action_type}", status_code=status.HTTP_400_BAD_REQUEST)

    def confirm_action(
        self,
        conversation_id: str,
        action_id: str,
        approved: bool,
        rejection_reason: str | None,
        current_user: AppUser,
    ) -> ChatActionConfirmData:
        pending = self.audit_repo.find_pending_action(action_id, current_user.id, conversation_id)
        if not pending or not pending.action_type or not pending.payload:
            raise AppException("Pending action not found", status_code=status.HTTP_404_NOT_FOUND)

        if not approved:
            self._create_audit(
                event_type="CHAT_ACTION_REJECTED",
                user_id=current_user.id,
                conversation_id=conversation_id,
                action_id=action_id,
                action_type=pending.action_type,
                status="REJECTED",
                metadata={"rejection_reason": rejection_reason} if rejection_reason else None,
            )
            return ChatActionConfirmData(
                conversation_id=conversation_id,
                action_id=action_id,
                status="REJECTED",
                reply="Acción cancelada. No se realizó ningún cambio.",
            )

        can_confirm_action(current_user, pending.action_type)
        self._create_audit(
            event_type="CHAT_ACTION_APPROVED",
            user_id=current_user.id,
            conversation_id=conversation_id,
            action_id=action_id,
            action_type=pending.action_type,
            status="APPROVED",
        )

        try:
            result = self._execute_pending_action(pending.action_type, pending.payload, current_user)
            self._create_audit(
                event_type="CHAT_ACTION_EXECUTED",
                user_id=current_user.id,
                conversation_id=conversation_id,
                action_id=action_id,
                action_type=pending.action_type,
                result=result,
                status="SUCCESS",
            )
            reply = self._build_success_reply(pending.action_type, result)
            return ChatActionConfirmData(
                conversation_id=conversation_id,
                action_id=action_id,
                status="APPROVED",
                reply=reply,
                result=result,
            )
        except AppException as exc:
            self._create_audit(
                event_type="CHAT_ACTION_FAILED",
                user_id=current_user.id,
                conversation_id=conversation_id,
                action_id=action_id,
                action_type=pending.action_type,
                error_message=exc.message,
                status="FAILED",
            )
            raise

    def _build_success_reply(self, action_type: str, result: dict[str, Any]) -> str:
        if action_type == "generate_monthly_purchase_orders":
            generated = result.get("generated_count", 0)
            skipped = result.get("skipped_count", 0)
            return f"Listo. Se generaron {generated} OCs mensuales para la asignación seleccionada. Omitidas: {skipped}."
        if action_type == "update_purchase_order_status":
            return f"Listo. La orden de compra fue actualizada a estado {result.get('status')}."
        return "Acción ejecutada correctamente."
