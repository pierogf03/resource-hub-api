from app.schemas.ai_chat_api_schema import AssistantSkillInfo

ASSISTANT_SKILLS: list[AssistantSkillInfo] = [
    AssistantSkillInfo(
        skill="get_dashboard_summary",
        internal_endpoint="GET /internal/workato/dashboard-summary",
        description="General status and executive summary for the user's scoped portfolio.",
        supported_queries=[
            "general status",
            "executive summaries",
            "active assignments",
            "expiration counts",
            "purchase order counts",
            "overall committed cost",
        ],
    ),
    AssistantSkillInfo(
        skill="get_expiring_resources",
        internal_endpoint="GET /internal/workato/expiring-resources",
        description="Expiration alerts and contracts ending soon within the user's scope.",
        supported_queries=[
            "expired resources",
            "resources about to expire",
            "RED alerts",
            "AMBER alerts",
            "renewals",
            "contracts ending soon",
        ],
    ),
    AssistantSkillInfo(
        skill="search_assignments",
        internal_endpoint="GET /internal/workato/assignments",
        description="Search and lookup assignments by consultant, profile, provider, or initiative.",
        supported_queries=[
            "consultant searches",
            "technical profiles",
            "providers",
            "initiatives",
            "assignment details",
            "assignment lookup",
        ],
    ),
    AssistantSkillInfo(
        skill="get_purchase_orders_status",
        internal_endpoint="GET /internal/workato/purchase-orders",
        description="Purchase order status, counts, and filtered listings.",
        supported_queries=[
            "purchase order status",
            "pending OCs",
            "approved OCs",
            "closed OCs",
            "Coupa generated OCs",
            "sent OCs",
            "purchase orders by month",
            "purchase orders by provider",
            "purchase orders by assignment",
            "purchase orders by consultant",
        ],
    ),
    AssistantSkillInfo(
        skill="get_budget_summary",
        internal_endpoint="GET /internal/workato/budget-summary",
        description="Committed budget and cost breakdowns in USD.",
        supported_queries=[
            "committed budget",
            "monthly cost",
            "cost by initiative",
            "cost by provider",
            "cost by manager",
        ],
    ),
    AssistantSkillInfo(
        skill="get_import_status",
        internal_endpoint="GET /internal/workato/import-status",
        description="Historical Excel import batches, latest status, and row-level errors.",
        supported_queries=[
            "historical Excel imports",
            "latest import status",
            "successful rows",
            "failed rows",
            "import errors",
        ],
    ),
]
