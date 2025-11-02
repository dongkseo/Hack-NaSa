"""
API v1 Router

Aggregates all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import predictions, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(health.router, tags=["Health"])
