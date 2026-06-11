from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.import_schema import ImportBatchListItem, ImportErrorItem
from app.services.excel_import_service import ExcelImportService

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/historical-excel")
async def import_historical_excel(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    file: UploadFile = File(...),
    default_manager_id: UUID | None = Form(default=None),
    default_exchange_rate: Decimal | None = Form(default=None),
    auto_generate_purchase_orders: bool = Form(default=True),
):
    file_bytes = await file.read()
    result = ExcelImportService(db).import_historical_excel(
        current_user,
        file.filename or "import.xlsx",
        file_bytes,
        default_manager_id,
        default_exchange_rate,
        auto_generate_purchase_orders,
    )
    return success_response("Historical Excel import completed", result.model_dump())


@router.get("")
def list_imports(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = ExcelImportService(db).list_batches(page, page_size)
    data = {
        "items": [ImportBatchListItem.model_validate(item).model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Import batches retrieved successfully", data)


@router.get("/{batch_id}/errors")
def list_import_errors(
    batch_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    errors = ExcelImportService(db).list_errors(batch_id)
    data = [
        ImportErrorItem(
            row_number=error.row_number,
            column_name=error.column_name,
            error_message=error.error_message,
            raw_data=error.raw_data,
        ).model_dump()
        for error in errors
    ]
    return success_response("Import errors retrieved successfully", data)
