
"""Seed demo data for Resource Hub. All consultant and provider names are fictitious."""
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
            print("Seed skipped: data already exists. Run the truncate script before seeding again.")
            return

        # ============================================================
        # USERS
        # ============================================================

        admin = AppUser(
            full_name="Piero Gonzales",
            email="pierogonzales@belcorp.biz",
            password_hash=hash_password("123456789"),
            role="ADMIN",
        )

        manager_1 = AppUser(
            full_name="Sylma Huerta",
            email="sylmahuerta@belcorp.biz",
            password_hash=hash_password("123456789"),
            role="MANAGER",
        )

        manager_2 = AppUser(
            full_name="Geovanny Alberto Vergara",
            email="geovannyvergara@belcorp.biz",
            password_hash=hash_password("123456789"),
            role="MANAGER",
        )

        manager_3 = AppUser(
            full_name="Javier Cullas",
            email="jcullas@belcorp.com",
            password_hash=hash_password("123456789"),
            role="MANAGER",
        )

        users = [admin, manager_1, manager_2, manager_3]
        db.add_all(users)
        db.flush()

        managers = [manager_1, manager_2, manager_3]

        # ============================================================
        # PROVIDERS
        # ============================================================

        providers = [
            Provider(name="Proveedor Demo SAP Enterprise", contact_name="Contacto SAP", contact_email="sap.demo@proveedor.local"),
            Provider(name="Proveedor Demo Workato Integrations", contact_name="Contacto Workato", contact_email="workato.demo@proveedor.local"),
            Provider(name="Proveedor Demo Full Stack Delivery", contact_name="Contacto Full Stack", contact_email="fullstack.demo@proveedor.local"),
            Provider(name="Proveedor Demo BW Analytics", contact_name="Contacto BW", contact_email="bw.demo@proveedor.local"),
            Provider(name="Proveedor Demo Data Platform", contact_name="Contacto Data", contact_email="data.demo@proveedor.local"),
            Provider(name="Proveedor Demo QA Automation", contact_name="Contacto QA", contact_email="qa.demo@proveedor.local"),
        ]

        db.add_all(providers)
        db.flush()

        # ============================================================
        # INITIATIVES
        # ============================================================

        initiatives = [
            Initiative(
                name="Implementación SAP Finance",
                description="Implementación y estabilización de procesos SAP Finance.",
                responsible_manager_id=manager_1.id,
                budget_usd=Decimal("65000.00"),
            ),
            Initiative(
                name="Automatización Workato & Coupa",
                description="Automatización de integraciones Workato y flujo de órdenes de compra Coupa.",
                responsible_manager_id=manager_2.id,
                budget_usd=Decimal("45000.00"),
            ),
            Initiative(
                name="Finance Platform Core",
                description="Evolución de componentes core de la plataforma financiera.",
                responsible_manager_id=manager_3.id,
                budget_usd=Decimal("55000.00"),
            ),
            Initiative(
                name="Migración BW Analytics",
                description="Migración y optimización de modelos BW y reporting analítico.",
                responsible_manager_id=manager_1.id,
                budget_usd=Decimal("35000.00"),
            ),
            Initiative(
                name="Integraciones SAP Legacy",
                description="Integraciones entre SAP, sistemas legacy y servicios internos.",
                responsible_manager_id=manager_2.id,
                budget_usd=Decimal("38000.00"),
            ),
            Initiative(
                name="Control Presupuestal Externos",
                description="Seguimiento presupuestal de recursos externos y costos comprometidos.",
                responsible_manager_id=manager_3.id,
                budget_usd=Decimal("30000.00"),
            ),
        ]

        db.add_all(initiatives)
        db.flush()

        # ============================================================
        # EXTERNAL RESOURCES
        # ============================================================

        resource_specs = [
            ("Consultor Demo ABAP Senior", "ABAP"),
            ("Consultor Demo FI Funcional", "FI"),
            ("Consultor Demo Full Stack Angular", "Full Stack"),
            ("Consultor Demo Workato Specialist", "Workato"),
            ("Consultor Demo BW Reporting", "BW"),
            ("Consultor Demo QA Automation", "QA"),
            ("Consultor Demo Data Engineer", "Data"),
            ("Consultor Demo Integraciones SAP", "Integraciones SAP"),
            ("Consultor Demo Backend Python", "Backend Python"),
            ("Consultor Demo Frontend Angular", "Frontend Angular"),
            ("Consultor Demo SAP Basis", "SAP Basis"),
            ("Consultor Demo Coupa Analyst", "Coupa"),
            ("Consultor Demo RPA Finance", "RPA"),
            ("Consultor Demo API Integration", "API Integration"),
            ("Consultor Demo Power BI", "Power BI"),
            ("Consultor Demo DevOps Cloud", "DevOps"),
            ("Consultor Demo Data Quality", "Data Quality"),
            ("Consultor Demo Security Analyst", "Security"),
        ]

        resources = [
            ExternalResource(consultant_name=name, technical_profile=profile)
            for name, profile in resource_specs
        ]

        db.add_all(resources)
        db.flush()

        today = date.today()

        # ============================================================
        # ASSIGNMENTS
        # Dynamic dates relative to today for a fresh demo:
        # - Expired / RED
        # - RED upcoming
        # - AMBER
        # - GREEN
        # - USD and PEN
        # - Multiple managers
        # ============================================================

        assignment_specs = [
            # resource, provider, initiative, manager, monthly_cost, currency, exchange_rate, start, end, comments, extra_initiative
            (0, 0, 0, 0, Decimal("4200.00"), "USD", None, today - timedelta(days=95), today - timedelta(days=3), "Asignación vencida. Requiere decisión de renovación o cierre.", None),
            (1, 0, 0, 0, Decimal("15500.00"), "PEN", Decimal("3.75"), today - timedelta(days=70), today + timedelta(days=5), "Recurso crítico FI. Costo registrado en PEN y normalizado a USD.", 3),
            (2, 2, 2, 2, Decimal("3800.00"), "USD", None, today - timedelta(days=40), today + timedelta(days=9), "Frontend Angular para Finance Platform. Próximo a vencer.", None),
            (3, 1, 1, 1, Decimal("3600.00"), "USD", None, today - timedelta(days=20), today + timedelta(days=18), "Especialista Workato para automatización Coupa.", 4),
            (4, 3, 3, 0, Decimal("3400.00"), "USD", None, today - timedelta(days=30), today + timedelta(days=24), "Soporte BW Analytics con alerta ámbar.", None),
            (5, 5, 2, 2, Decimal("7200.00"), "PEN", Decimal("3.80"), today - timedelta(days=15), today + timedelta(days=38), "QA Automation para pruebas de plataforma.", None),
            (6, 4, 5, 2, Decimal("4500.00"), "USD", None, today - timedelta(days=60), today + timedelta(days=65), "Data Engineer para control presupuestal.", 2),
            (7, 1, 4, 1, Decimal("3900.00"), "USD", None, today - timedelta(days=45), today + timedelta(days=75), "Integraciones SAP Legacy.", None),
            (8, 2, 2, 2, Decimal("4100.00"), "USD", None, today - timedelta(days=10), today + timedelta(days=120), "Backend Python para Resource Hub y servicios financieros.", None),
            (9, 2, 2, 2, Decimal("3700.00"), "USD", None, today - timedelta(days=5), today + timedelta(days=145), "Frontend Angular para módulos core.", None),
            (10, 0, 0, 0, Decimal("5200.00"), "USD", None, today - timedelta(days=110), today + timedelta(days=2), "SAP Basis en estado rojo. Revisión inmediata.", None),
            (11, 1, 1, 1, Decimal("3300.00"), "USD", None, today - timedelta(days=25), today + timedelta(days=50), "Analista Coupa para seguimiento de OCs.", None),
            (12, 4, 5, 2, Decimal("12500.00"), "PEN", Decimal("3.75"), today - timedelta(days=75), today + timedelta(days=88), "RPA Finance con costo PEN.", None),
            (13, 1, 4, 1, Decimal("3950.00"), "USD", None, today - timedelta(days=30), today + timedelta(days=115), "API Integration para SAP Legacy.", 1),
            (14, 3, 3, 0, Decimal("3100.00"), "USD", None, today - timedelta(days=50), today + timedelta(days=140), "Power BI para reporting financiero.", None),
            (15, 2, 2, 2, Decimal("4600.00"), "USD", None, today - timedelta(days=15), today + timedelta(days=170), "DevOps Cloud para despliegues y monitoreo.", None),
            (16, 4, 5, 2, Decimal("2950.00"), "USD", None, today - timedelta(days=20), today - timedelta(days=1), "Data Quality vencido. Debe cerrarse o renovarse.", None),
            (17, 5, 5, 2, Decimal("2850.00"), "USD", None, today - timedelta(days=7), today + timedelta(days=12), "Security Analyst en alerta roja.", None),
        ]

        current_month = first_day_of_month(today)
        po_counter = 1

        def select_po_status(period_month: date, assignment_index: int) -> str:
            period = first_day_of_month(period_month)

            if period < current_month:
                historical_statuses = ["APPROVED", "CLOSED", "SENT"]
                return historical_statuses[(po_counter + assignment_index) % len(historical_statuses)]

            if period == current_month:
                current_statuses = ["PENDING", "COUPA_GENERATED", "SENT", "APPROVED"]
                return current_statuses[(po_counter + assignment_index) % len(current_statuses)]

            future_statuses = ["PENDING", "COUPA_GENERATED"]
            return future_statuses[(po_counter + assignment_index) % len(future_statuses)]

        for index, (
            resource_idx,
            provider_idx,
            initiative_idx,
            manager_idx,
            monthly_cost,
            currency,
            exchange_rate,
            start_date,
            end_date,
            comments,
            extra_initiative_idx,
        ) in enumerate(assignment_specs):
            periods = months_in_range(start_date, end_date)
            duration_months = max(len(periods), 1)

            monthly_cost_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)
            total_cost_usd = calculate_total_cost_usd(monthly_cost_usd, duration_months)

            assignment = ResourceAssignment(
                resource_id=resources[resource_idx].id,
                provider_id=providers[provider_idx].id,
                main_initiative_id=initiatives[initiative_idx].id,
                manager_id=managers[manager_idx].id,
                analyst_responsible_id=managers[manager_idx].id,
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

            db.add(assignment)
            db.flush()

            if extra_initiative_idx is not None:
                db.add_all(
                    [
                        ResourceAssignmentInitiative(
                            assignment_id=assignment.id,
                            initiative_id=initiatives[initiative_idx].id,
                            allocation_percentage=Decimal("80"),
                            is_primary=True,
                            is_funding_source=True,
                        ),
                        ResourceAssignmentInitiative(
                            assignment_id=assignment.id,
                            initiative_id=initiatives[extra_initiative_idx].id,
                            allocation_percentage=Decimal("20"),
                            is_primary=False,
                            is_funding_source=False,
                        ),
                    ]
                )
            else:
                db.add(
                    ResourceAssignmentInitiative(
                        assignment_id=assignment.id,
                        initiative_id=initiatives[initiative_idx].id,
                        allocation_percentage=Decimal("100"),
                        is_primary=True,
                        is_funding_source=True,
                    )
                )

            for period_month in periods:
                status = select_po_status(period_month, index)
                amount_usd = calculate_monthly_cost_usd(monthly_cost, currency, exchange_rate)

                po = PurchaseOrder(
                    assignment_id=assignment.id,
                    provider_id=providers[provider_idx].id,
                    period_month=first_day_of_month(period_month),
                    status=status,
                    amount=monthly_cost,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    amount_usd=amount_usd,
                    po_number=f"OC-RH-{today.year}-{po_counter:04d}",
                    comments=f"OC demo generada para {resources[resource_idx].consultant_name}",
                )

                db.add(po)
                po_counter += 1

        db.commit()
        print("Resource Hub demo seed data loaded successfully.")
        print("")
        print("Demo users:")
        print("Admin   -> pierogonzales@belcorp.biz / Admin123")
        print("Manager -> sylmahuerta@belcorp.biz / Manager123")
        print("Manager -> geovannyvergara@belcorp.biz / Manager123")
        print("Manager -> jcullas@belcorp.com / Manager123")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

