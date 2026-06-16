from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.ai_chat_api_schema import ChatActionConfirmRequest, ChatMessageRequest
from app.schemas.common_schema import success_response
from app.services.ai_chat_api_service import AiChatApiService
from app.services.assistant_skills import ASSISTANT_SKILLS

router = APIRouter(prefix="/ai/chat", tags=["Resource Hub Assistant"])


@router.get("/skills")
def list_assistant_skills(
    _: Annotated[AppUser, Depends(get_current_user)],
):
    return success_response(
        "Assistant skills retrieved successfully",
        [skill.model_dump() for skill in ASSISTANT_SKILLS],
    )


@router.post("/messages")
def send_chat_message(
    payload: ChatMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    result = AiChatApiService(db).send_message(
        payload.message,
        payload.conversation_id,
        current_user,
        payload.metadata,
    )
    return success_response("Assistant response retrieved successfully", result.model_dump(mode="json"))


@router.post("/actions/confirm")
def confirm_chat_action(
    payload: ChatActionConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    result = AiChatApiService(db).confirm_action(
        payload.conversation_id,
        payload.action_id,
        payload.approved,
        payload.rejection_reason,
        current_user,
    )
    message = "Action confirmation processed successfully" if payload.approved else "Action rejected successfully"
    return success_response(message, result.model_dump(mode="json"))
