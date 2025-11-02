"""
Schemas Package

Pydantic schemas for request/response validation (DTOs)
"""
from .prediction import (
    PredictionRequest,
    PredictionResponse,
    ConnectionStatusResponse
)

__all__ = [
    "PredictionRequest",
    "PredictionResponse",
    "ConnectionStatusResponse"
]
