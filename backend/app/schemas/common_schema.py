from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: str
    message: str


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def success_response(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}
