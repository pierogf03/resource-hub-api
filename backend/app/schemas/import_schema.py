from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImportCreatedSummary(BaseModel):
    providers: int
    initiatives: int
    external_resources: int
    assignments: int
    purchase_orders: int


class ImportErrorItem(BaseModel):
    row_number: int
    column_name: str | None
    error_message: str
    raw_data: dict | None = None


class ImportResultResponse(BaseModel):
    batch_id: UUID
    file_name: str
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    created: ImportCreatedSummary
    errors: list[ImportErrorItem]


class ImportBatchListItem(BaseModel):
    id: UUID
    file_name: str
    imported_by: UUID
    total_rows: int
    successful_rows: int
    failed_rows: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
