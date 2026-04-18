from fastapi import APIRouter

from app.api.routes import auth, health, telegram, webhooks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])

