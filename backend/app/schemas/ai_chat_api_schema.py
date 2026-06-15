from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def validate_message_length(cls, value: str) -> str:
        max_length = get_settings().AI_CHAT_MAX_MESSAGE_LENGTH
        if len(value) > max_length:
            raise ValueError(f"Message cannot exceed {max_length} characters")
        return value


class ChatActionConfirmRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    approved: bool
    rejection_reason: str | None = None


class PendingAction(BaseModel):
    action_id: str
    action_type: str
    summary: str
    payload: dict[str, Any]


class ChatMessageData(BaseModel):
    conversation_id: str
    reply: str
    intent: str
    used_skills: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    pending_action: PendingAction | None = None
    created_at: datetime


class ChatActionConfirmData(BaseModel):
    conversation_id: str
    action_id: str
    status: str
    reply: str
    result: dict[str, Any] | None = None


class WorkatoUserContext(BaseModel):
    id: str
    full_name: str
    email: str
    role: str


class WorkatoResourceHubContext(BaseModel):
    app_name: str = "Resource Hub"
    source: str = "web"
    permissions_mode: str = "backend_enforced"
    allowed_capabilities: list[str]


class WorkatoChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user: WorkatoUserContext
    resource_hub_context: WorkatoResourceHubContext
    metadata: dict[str, Any] | None = None


class WorkatoPendingAction(BaseModel):
    action_id: str
    action_type: str
    summary: str
    payload: dict[str, Any]


class WorkatoErrorDetail(BaseModel):
    code: str
    message: str


class WorkatoChatResponse(BaseModel):
    model_config = {"extra": "ignore"}

    conversation_id: str
    reply: str
    intent: str = "unknown"
    used_skills: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    pending_action: WorkatoPendingAction | None = None
    error: WorkatoErrorDetail | None = None


class ImportBatchSummaryItem(BaseModel):
    batch_id: UUID
    file_name: str
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    created_at: datetime


class ImportErrorSummaryItem(BaseModel):
    row_number: int
    column_name: str | None
    error_message: str


class ImportStatusResponse(BaseModel):
    batch_id: UUID | None = None
    file_name: str | None = None
    status: str | None = None
    total_rows: int | None = None
    successful_rows: int | None = None
    failed_rows: int | None = None
    created_at: datetime | None = None
    errors: list[ImportErrorSummaryItem] = Field(default_factory=list)
    recent_batches: list[ImportBatchSummaryItem] = Field(default_factory=list)


class AssistantSkillInfo(BaseModel):
    skill: str
    internal_endpoint: str
    description: str
    supported_queries: list[str]


class PurchaseOrderStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(PENDING|COUPA_GENERATED|SENT|APPROVED|CLOSED|CANCELLED)$")
    comments: str | None = None
    po_number: str | None = Field(default=None, max_length=80)
