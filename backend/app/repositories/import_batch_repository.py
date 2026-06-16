from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.import_batch import ImportBatch, ImportBatchError


class ImportBatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, batch_id: UUID) -> ImportBatch | None:
        return self.db.scalar(
            select(ImportBatch).options(joinedload(ImportBatch.errors)).where(ImportBatch.id == batch_id)
        )

    def list_batches(self, page: int, page_size: int):
        query = select(ImportBatch)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(ImportBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return items, total

    def create(self, batch: ImportBatch) -> ImportBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def update(self, batch: ImportBatch) -> ImportBatch:
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def add_error(self, error: ImportBatchError) -> None:
        self.db.add(error)
        self.db.commit()

    def list_errors(self, batch_id: UUID) -> list[ImportBatchError]:
        return self.db.scalars(
            select(ImportBatchError).where(ImportBatchError.batch_id == batch_id).order_by(ImportBatchError.row_number)
        ).all()

    def get_latest_batch(self) -> ImportBatch | None:
        return self.db.scalar(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(1))

    def list_recent_batches(self, limit: int = 5) -> list[ImportBatch]:
        return list(
            self.db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(limit)).all()
        )
