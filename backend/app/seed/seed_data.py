"""Seed demo data for Resoruse Hub. All provider and user names are fictitious."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.external_resource import ExternalResource
from app.models.initiative import Initiative
from app.models.provider import Provider
from app.models.purchase_order import PurchaseOrder
from app.models.resource_assignment import ResourceAssignment, ResourceAssignmentInitiative
from app.models.user import AppUser
from app.utils.date_utils import first_day_of_month, months_in_range
from app.utils.money_utils import calculate_monthly_cost_usd, calculate_total_cost_usd


def seed() -> None:
    db = SessionLocal()
    try:
        if (db.scalar(select(func.count()).select_from(AppUser)) or 0) > 0:
            print("Seed skipped: data already exists.")
            return

        users = [
            AppUser(full_name="Admin Demo", email="admin@resorusehub.com", password_hash=hash_password("Admin123"), role="ADMIN"),
            AppUser(full_name="Manager Demo 01", email="manager1@resorusehub.com", password_hash=hash_password("Manager123"), role="MANAGER"),
            AppUser(full_name="Manager Demo 02", email="manager2@resorusehub.com", password_hash=hash_password("Manager123"), role="MANAGER"),
            AppUser(full_name="Manager Demo 03", email="manager3@resorusehub.com", password_hash=hash_password("Manager123"), role="MANAGER"),
            AppUser(full_name="Analista Demo 01", email="analyst1@resorusehub.com", password_hash=hash_password("Analyst123"), role="ANALYST"),
            AppUser(full_name="Analista Demo 02", email="analyst2@resorusehub.com", password_hash=hash_password("Analyst123"), role="ANALYST"),
        ]
        db.add_all(users)
        db.flush()

        providers = [
            Provider(name="Proveedor Demo SAP"),
            Provider(name="Proveedor Demo Workato"),
            Provider(name="Proveedor Demo Full Stack"),
            Provider(name="Proveedor Demo BW"),
            Provider(name="Proveedor Demo Data Analytics"),
        ]
        db.add_all(providers)
        db.flush()

        managers = [u for u in users if u.role == "MANAGER"]
        analysts = [u for u in users if u.role == "ANALYST"]

        initiatives = [
            Initiative(name="Implementación SAP", description="Proyecto de implementación SAP", responsible_manager_id=managers[0].id, budget_usd=Decimal("50000")),
            Initiative(name="Integraciones Workato", description="Automatización de integraciones", responsible_manager_id=managers[1].id, budget_usd=Decimal("30000")),
            Initiative(name="Finance Platform", description="Plataforma financiera", responsible_manager_id=managers[2].id, budget_usd=Decimal("40000")),
            Initiative(name="Migración BW", description="Migración de BW", responsible_manager_id=managers[0].id, budget_usd=Decimal("25000")),
            Initiative(name="Automatización Coupa", description="Automatización de compras", responsible_manager_id=managers[1].id, budget_usd=Decimal("20000")),
        ]
        db.add_all(initiatives)
        db.flush()

        profiles = [
            ("Consultor Demo ABAP", "ABAP"),
            ("Consultor Demo FI", "FI"),
            ("Consultor Demo Full Stack", "Full Stack"),
            ("Consultor Demo Workato", "Workato"),
            ("Consultor Demo BW", "BW"),
            ("Consultor Demo QA", "QA"),
            ("Consultor Demo Data", "Data"),
            ("Consultor Demo Integraciones SAP", "Integraciones SAP"),
            ("Consultor Demo Backend Python", "Backend Python"),
            ("Consultor Demo Frontend Angular", "Frontend Angular"),
        ]
        resources = [ExternalResource(consultant_name=name, technical_profile=profile) for name, profile in profiles]
        db.add_all(resources)
        db.flush()

        today = date.today()
        assignment_specs = [
            (0, 0, 0, 1, Decimal("2500"), "USD", None, today, today + timedelta(days=5)),
            (1, 1, 1, 3, Decimal("3000"), "USD", None, today - timedelta(days=30), today + timedelta(days=20)),
            (2, 2, 2, 6, Decimal("1800"), "PEN", Decimal("3.75"), today - timedelta(days=60), today + timedelta(days=45)),
            (3, 3, 0, 8, Decimal("2200"), "USD", None, today - timedelta(days=90), today + timedelta(days=150)),
            (4, 4, 1, 3, Decimal("2700"), "USD", None, today - timedelta(days=15), today + timedelta(days=10)),
            (5, 0, 2, 1, Decimal("1500"), "PEN", Decimal("3.80"), today, today + timedelta(days=25)),
            (6, 1, 0, 6, Decimal("3200"), "USD", None, today - timedelta(days=45), today + timedelta(days=60)),
            (7, 2, 1, 3, Decimal("2900"), "USD", None, today - timedelta(days=10), today + timedelta(days=18)),
            (8, 3, 2, 8, Decimal("2100"), "USD", None, today - timedelta(days=120), today + timedelta(days=200)),
            (9, 4, 0, 1, Decimal("2600"), "USD", None, today - timedelta(days=5), today + timedelta(days=2)),
        ]

        po_statuses = ["PENDING", "COUPA_GENERATED", "SENT", "APPROVED", "CLOSED"]
        status_index = 0

        for resource_idx, provider_idx, initiative_idx, duration, monthly_cost, currency, exchange_rate, start_date, end_date in assignment_specs:
            monthly_cost_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
            total_cost_usd = calculate_total_cost_usd(monthly_cost_usd, duration)
            assignment = ResourceAssignment(
                resource_id=resources[resource_idx].id,
                provider_id=providers[provider_idx].id,
                main_initiative_id=initiatives[initiative_idx].id,
                manager_id=managers[initiative_idx % len(managers)].id,
                analyst_responsible_id=analysts[resource_idx % len(analysts)].id,
                start_date=start_date,
                end_date=end_date,
                duration_months=duration,
                monthly_cost=monthly_cost,
                currency=currency,
                exchange_rate=exchange_rate,
                monthly_cost_usd=monthly_cost_usd,
                total_cost_usd=total_cost_usd,
                status="ACTIVE",
                comments="Asignación demo",
            )
            db.add(assignment)
            db.flush()
            db.add(
                ResourceAssignmentInitiative(
                    assignment_id=assignment.id,
                    initiative_id=initiatives[initiative_idx].id,
                    allocation_percentage=Decimal("100"),
                    is_primary=True,
                    is_funding_source=True,
                )
            )
            for period_month in months_in_range(start_date, end_date):
                amount_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
                po = PurchaseOrder(
                    assignment_id=assignment.id,
                    provider_id=providers[provider_idx].id,
                    period_month=first_day_of_month(period_month),
                    status=po_statuses[status_index % len(po_statuses)],
                    amount=monthly_cost,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    amount_usd=amount_usd,
                    po_number=f"OC-DEMO-{status_index + 1:03d}",
                )
                db.add(po)
                status_index += 1

        db.commit()
        print("Seed data loaded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
