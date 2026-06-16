from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.routers import (
    ai_chat_api,
    assignments,
    auth,
    dashboard,
    exchange_rates,
    external_resources,
    imports,
    initiatives,
    providers,
    purchase_orders,
    users,
    workato_internal,
)

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(providers.router)
app.include_router(initiatives.router)
app.include_router(external_resources.router)
app.include_router(assignments.router)
app.include_router(purchase_orders.router)
app.include_router(dashboard.router)
app.include_router(exchange_rates.router)
app.include_router(imports.router)
app.include_router(ai_chat_api.router)
app.include_router(workato_internal.router)


@app.get("/health")
def health_check():
    return {"success": True, "message": "Service is healthy", "data": {"status": "ok"}}
