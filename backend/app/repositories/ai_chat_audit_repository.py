from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.ai_chat_audit import AiChatAuditLog


class AiChatAuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        *,
        event_type: str,
        user_id: UUID | None = None,
        conversation_id: str | None = None,
        message: str | None = None,
        reply: str | None = None,
        intent: str | None = None,
        used_skills: list | None = None,
        action_id: str | None = None,
        action_type: str | None = None,
        payload: dict | None = None,
        result: dict | None = None,
        metadata: dict | None = None,
        status: str | None = None,
        error_message: str | None = None,
    ) -> AiChatAuditLog:
        log = AiChatAuditLog(
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            message=message,
            reply=reply,
            intent=intent,
            used_skills=used_skills,
            action_id=action_id,
            action_type=action_type,
            payload=payload,
            result=result,
            metadata_=metadata,
            status=status,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def find_pending_action(
        self, action_id: str, user_id: UUID, conversation_id: str
    ) -> AiChatAuditLog | None:
        return self.db.scalar(
            select(AiChatAuditLog)
            .where(
                AiChatAuditLog.event_type == "CHAT_ACTION_PENDING",
                AiChatAuditLog.status == "PENDING_APPROVAL",
                AiChatAuditLog.action_id == action_id,
                AiChatAuditLog.user_id == user_id,
                AiChatAuditLog.conversation_id == conversation_id,
            )
            .order_by(desc(AiChatAuditLog.created_at))
            .limit(1)
        )

    def list_by_conversation(self, conversation_id: str, user_id: UUID) -> list[AiChatAuditLog]:
        return list(
            self.db.scalars(
                select(AiChatAuditLog)
                .where(
                    AiChatAuditLog.conversation_id == conversation_id,
                    AiChatAuditLog.user_id == user_id,
                )
                .order_by(desc(AiChatAuditLog.created_at))
            ).all()
        )
