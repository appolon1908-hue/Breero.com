from fastapi import APIRouter

from app.api.v2 import capabilities

api_router = APIRouter()
api_router.include_router(capabilities.router, tags=["capabilities"])
