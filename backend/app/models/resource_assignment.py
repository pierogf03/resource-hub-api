import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResourceAssignment(Base):
    __tablename__ = "resource_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("external_resources.id"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    main_initiative_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("initiatives.id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_users.id"), nullable=False)
    analyst_responsible_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.id"), nullable=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    monthly_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    resource = relationship("ExternalResource", back_populates="assignments")
    provider = relationship("Provider", back_populates="assignments")
    main_initiative = relationship("Initiative", back_populates="main_assignments", foreign_keys=[main_initiative_id])
    manager = relationship("AppUser", back_populates="managed_assignments", foreign_keys=[manager_id])
    analyst_responsible = relationship("AppUser", back_populates="analyst_assignments", foreign_keys=[analyst_responsible_id])
    initiative_allocations = relationship("ResourceAssignmentInitiative", back_populates="assignment", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="assignment", cascade="all, delete-orphan")


class ResourceAssignmentInitiative(Base):
    __tablename__ = "resource_assignment_initiatives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resource_assignments.id"), nullable=False)
    initiative_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("initiatives.id"), nullable=False)
    allocation_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_funding_source: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment = relationship("ResourceAssignment", back_populates="initiative_allocations")
    initiative = relationship("Initiative", back_populates="assignment_allocations")
