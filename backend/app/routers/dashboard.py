from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    summary = DashboardService(db).get_summary(current_user)
    return success_response("Dashboard summary retrieved successfully", summary.model_dump())


@router.get("/expiring-resources")
def expiring_resources(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    items = DashboardService(db).get_expiring_resources(current_user)
    return success_response(
        "Expiring resources retrieved successfully",
        [item.model_dump() for item in items],
    )
