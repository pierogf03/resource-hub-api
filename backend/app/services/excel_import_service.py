from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.import_batch import ImportBatch, ImportBatchError
from app.models.purchase_order import PurchaseOrder
from app.models.resource_assignment import ResourceAssignment, ResourceAssignmentInitiative
from app.models.user import AppUser
from app.repositories.import_batch_repository import ImportBatchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ai_chat_api_schema import (
    ImportBatchSummaryItem,
    ImportErrorSummaryItem,
    ImportStatusResponse,
)
from app.schemas.import_schema import ImportCreatedSummary, ImportErrorItem, ImportResultResponse
from app.services.assignment_service import AssignmentService
from app.services.external_resource_service import ExternalResourceService
from app.services.initiative_service import InitiativeService
from app.services.provider_service import ProviderService
from app.utils.date_utils import first_day_of_month, months_in_range
from app.utils.excel_utils import MONTH_COLUMNS, map_po_status, parse_date, parse_decimal, parse_excel_rows, parse_int
from app.utils.money_utils import calculate_monthly_cost_usd, calculate_total_cost_usd
from app.utils.string_utils import normalize_name


class ExcelImportService:
    def __init__(self, db: Session):
        self.db = db
        self.batch_repo = ImportBatchRepository(db)
        self.user_repo = UserRepository(db)
        self.provider_service = ProviderService(db)
        self.initiative_service = InitiativeService(db)
        self.resource_service = ExternalResourceService(db)
        self.assignment_service = AssignmentService(db)

    def list_batches(self, page: int, page_size: int):
        return self.batch_repo.list_batches(page, page_size)

    def list_errors(self, batch_id: UUID) -> list[ImportBatchError]:
        batch = self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise AppException("Import batch not found", status_code=404)
        return self.batch_repo.list_errors(batch_id)

    def get_import_status(self, current_user: AppUser, recent_limit: int = 5) -> ImportStatusResponse:
        _ = current_user
        batch = self.batch_repo.get_latest_batch()
        recent_batches = [
            ImportBatchSummaryItem(
                batch_id=item.id,
                file_name=item.file_name,
                status=item.status,
                total_rows=item.total_rows,
                successful_rows=item.successful_rows,
                failed_rows=item.failed_rows,
                created_at=item.created_at,
            )
            for item in self.batch_repo.list_recent_batches(recent_limit)
        ]
        if not batch:
            return ImportStatusResponse(recent_batches=recent_batches)

        errors = [
            ImportErrorSummaryItem(
                row_number=error.row_number,
                column_name=error.column_name,
                error_message=error.error_message,
            )
            for error in self.batch_repo.list_errors(batch.id)
        ]
        return ImportStatusResponse(
            batch_id=batch.id,
            file_name=batch.file_name,
            status=batch.status,
            total_rows=batch.total_rows,
            successful_rows=batch.successful_rows,
            failed_rows=batch.failed_rows,
            created_at=batch.created_at,
            errors=errors,
            recent_batches=recent_batches,
        )

    def get_latest_import_status(self, current_user: AppUser) -> ImportStatusResponse:
        return self.get_import_status(current_user)

    def import_historical_excel(
        self,
        current_user: AppUser,
        file_name: str,
        file_bytes: bytes,
        default_manager_id: UUID | None,
        default_exchange_rate: Decimal | None,
        auto_generate_purchase_orders: bool,
    ) -> ImportResultResponse:
        if not file_name.lower().endswith(".xlsx"):
            raise AppException("Only .xlsx files are supported")

        batch = ImportBatch(
            file_name=file_name,
            imported_by=current_user.id,
            status="PROCESSING",
        )
        batch = self.batch_repo.create(batch)

        created = ImportCreatedSummary(
            providers=0, initiatives=0, external_resources=0, assignments=0, purchase_orders=0
        )
        errors: list[ImportErrorItem] = []

        try:
            _, rows = parse_excel_rows(file_bytes)
        except ValueError as exc:
            batch.status = "FAILED"
            batch.error_summary = str(exc)
            batch.finished_at = datetime.now(timezone.utc)
            self.batch_repo.update(batch)
            raise AppException(str(exc))

        batch.total_rows = len(rows)
        successful_rows = 0
        failed_rows = 0

        for row in rows:
            row_number = row.get("_row_number", 0)
            try:
                result = self._process_row(
                    row,
                    default_manager_id,
                    default_exchange_rate,
                    auto_generate_purchase_orders,
                    created,
                )
                if result:
                    successful_rows += 1
            except AppException as exc:
                failed_rows += 1
                error = ImportBatchError(
                    batch_id=batch.id,
                    row_number=row_number,
                    column_name=exc.errors[0]["field"] if exc.errors else None,
                    error_message=exc.message,
                    raw_data={k: str(v) for k, v in row.items() if not k.startswith("_")},
                )
                self.batch_repo.add_error(error)
                errors.append(
                    ImportErrorItem(
                        row_number=row_number,
                        column_name=error.column_name,
                        error_message=error.error_message,
                    )
                )

        batch.successful_rows = successful_rows
        batch.failed_rows = failed_rows
        if failed_rows == 0:
            batch.status = "COMPLETED"
        elif successful_rows == 0:
            batch.status = "FAILED"
        else:
            batch.status = "COMPLETED_WITH_ERRORS"
        batch.finished_at = datetime.now(timezone.utc)
        self.batch_repo.update(batch)

        return ImportResultResponse(
            batch_id=batch.id,
            file_name=batch.file_name,
            status=batch.status,
            total_rows=batch.total_rows,
            successful_rows=batch.successful_rows,
            failed_rows=batch.failed_rows,
            created=created,
            errors=errors,
        )

    def _process_row(
        self,
        row: dict,
        default_manager_id: UUID | None,
        default_exchange_rate: Decimal | None,
        auto_generate_purchase_orders: bool,
        created: ImportCreatedSummary,
    ) -> bool:
        project_name = normalize_name(str(row.get("Proyecto") or ""))
        consultant_name = normalize_name(str(row.get("Consultor") or ""))
        provider_name = normalize_name(str(row.get("Proveedor") or ""))
        profile = normalize_name(str(row.get("Perfil") or ""))
        start_date = parse_date(row.get("Inicio"))
        end_date = parse_date(row.get("Fin"))
        duration_months = parse_int(row.get("Duración"))
        comments = str(row.get("Comentarios") or "").strip() or None

        if not project_name:
            raise AppException("Project is required", errors=[{"field": "Proyecto", "message": "Project is required"}])
        if not consultant_name:
            raise AppException("Consultant is required", errors=[{"field": "Consultor", "message": "Consultant is required"}])
        if not provider_name:
            raise AppException("Provider is required", errors=[{"field": "Proveedor", "message": "Provider is required"}])
        if not profile:
            raise AppException("Profile is required", errors=[{"field": "Perfil", "message": "Profile is required"}])
        if not start_date or not end_date:
            raise AppException("Start and end dates are required", errors=[{"field": "Inicio", "message": "Invalid dates"}])
        if end_date < start_date:
            raise AppException("End date must be after start date", errors=[{"field": "Fin", "message": "Invalid end date"}])
        if not duration_months or duration_months <= 0:
            raise AppException("Duration must be greater than 0", errors=[{"field": "Duración", "message": "Invalid duration"}])

        monthly_usd = parse_decimal(row.get("Costo Mensual [USD]"))
        monthly_pen = parse_decimal(row.get("Costo Mensual [PEN]"))
        currency = "USD"
        monthly_cost = monthly_usd or Decimal("0")
        exchange_rate = None
        if monthly_usd and monthly_usd > 0:
            currency = "USD"
            monthly_cost = monthly_usd
        elif monthly_pen and monthly_pen > 0:
            currency = "PEN"
            monthly_cost = monthly_pen
            exchange_rate = default_exchange_rate
            if not exchange_rate or exchange_rate <= 0:
                raise AppException(
                    "Exchange rate is required for PEN currency",
                    errors=[{"field": "Costo Mensual [PEN]", "message": "Exchange rate is required for PEN currency"}],
                )
        else:
            raise AppException("Monthly cost is required", errors=[{"field": "Costo Mensual [USD]", "message": "Cost required"}])

        provider, provider_created = self.provider_service.get_or_create_by_name(provider_name)
        if provider_created:
            created.providers += 1
        initiative, initiative_created = self.initiative_service.get_or_create_by_name(project_name)
        if initiative_created:
            created.initiatives += 1
        resource, resource_created = self.resource_service.get_or_create_by_name(consultant_name, profile)
        if resource_created:
            created.external_resources += 1

        manager_id = default_manager_id
        analyst_name = normalize_name(str(row.get("Analista responsable") or ""))
        analyst = self.user_repo.get_by_full_name(analyst_name) if analyst_name else None
        if not manager_id:
            if initiative.responsible_manager_id:
                manager_id = initiative.responsible_manager_id
            else:
                managers = [u for u in self.user_repo.list_users(None, "MANAGER", True, 1, 1)[0]]
                if not managers:
                    raise AppException("Default manager is required", errors=[{"field": "manager", "message": "Manager required"}])
                manager_id = managers[0].id

        monthly_cost_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
        total_cost_usd = calculate_total_cost_usd(monthly_cost_usd, duration_months)

        assignment = ResourceAssignment(
            resource_id=resource.id,
            provider_id=provider.id,
            main_initiative_id=initiative.id,
            manager_id=manager_id,
            analyst_responsible_id=analyst.id if analyst else None,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            monthly_cost=monthly_cost,
            currency=currency,
            exchange_rate=exchange_rate,
            monthly_cost_usd=monthly_cost_usd,
            total_cost_usd=total_cost_usd,
            status="ACTIVE",
            comments=comments,
        )
        allocation = ResourceAssignmentInitiative(
            initiative_id=initiative.id,
            allocation_percentage=Decimal("100"),
            is_primary=True,
            is_funding_source=True,
        )
        self.assignment_service.assignment_repo.create(assignment, [allocation])
        created.assignments += 1

        month_statuses = [map_po_status(row.get(col)) for col in MONTH_COLUMNS]
        has_month_statuses = any(str(row.get(col) or "").strip() for col in MONTH_COLUMNS)
        months = months_in_range(start_date, end_date)

        if has_month_statuses:
            for index, period_month in enumerate(months[: len(MONTH_COLUMNS)]):
                status = month_statuses[index]
                amount_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
                po = PurchaseOrder(
                    assignment_id=assignment.id,
                    provider_id=provider.id,
                    period_month=first_day_of_month(period_month),
                    status=status,
                    amount=monthly_cost,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    amount_usd=amount_usd,
                )
                self.db.add(po)
                self.db.commit()
                created.purchase_orders += 1
        elif auto_generate_purchase_orders:
            for period_month in months:
                amount_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
                po = PurchaseOrder(
                    assignment_id=assignment.id,
                    provider_id=provider.id,
                    period_month=first_day_of_month(period_month),
                    status="PENDING",
                    amount=monthly_cost,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    amount_usd=amount_usd,
                )
                self.db.add(po)
                self.db.commit()
                created.purchase_orders += 1

        return True
