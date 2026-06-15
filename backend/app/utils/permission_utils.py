from uuid import UUID

from fastapi import status

from app.core.exceptions import AppException
from app.models.resource_assignment import ResourceAssignment
from app.models.user import AppUser


def assert_assignment_access(assignment: ResourceAssignment, current_user: AppUser) -> None:
    if current_user.role == "ADMIN":
        return
    if current_user.role == "MANAGER":
        if assignment.manager_id != current_user.id:
            raise AppException("You do not have access to this assignment", status_code=status.HTTP_403_FORBIDDEN)
        return
    if assignment.analyst_responsible_id != current_user.id:
        raise AppException("You do not have access to this assignment", status_code=status.HTTP_403_FORBIDDEN)


def can_confirm_action(current_user: AppUser, action_type: str) -> None:
    if action_type == "generate_monthly_purchase_orders":
        if current_user.role not in {"ADMIN", "MANAGER"}:
            raise AppException(
                "Only managers and admins can generate monthly purchase orders",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return
    if action_type == "update_purchase_order_status":
        if current_user.role not in {"ADMIN", "MANAGER", "ANALYST"}:
            raise AppException(
                "You do not have permission to update purchase order status",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return
    raise AppException(f"Unsupported action type: {action_type}", status_code=status.HTTP_400_BAD_REQUEST)
