from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.user import AppUser


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> AppUser | None:
        return self.db.get(AppUser, user_id)

    def get_by_email(self, email: str) -> AppUser | None:
        return self.db.scalar(select(AppUser).where(func.lower(AppUser.email) == email.lower()))

    def get_by_full_name(self, full_name: str) -> AppUser | None:
        return self.db.scalar(select(AppUser).where(func.lower(AppUser.full_name) == full_name.strip().lower()))

    def list_users(self, search: str | None, role: str | None, is_active: bool | None, page: int, page_size: int):
        query = select(AppUser)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                or_(func.lower(AppUser.full_name).like(pattern), func.lower(AppUser.email).like(pattern))
            )
        if role:
            query = query.where(AppUser.role == role)
        if is_active is not None:
            query = query.where(AppUser.is_active == is_active)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(AppUser.full_name).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return items, total

    def create(self, user: AppUser) -> AppUser:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(AppUser)) or 0
