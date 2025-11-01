"""
Health Check Endpoints

시스템 상태 확인 엔드포인트
"""
import logging
from datetime import datetime
from fastapi import APIRouter
from app.core.dependencies import ConnectionRepo
from app.schemas.prediction import ConnectionStatusResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def read_root():
    """
    API 정보

    기본 엔드포인트 정보 제공
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "websocket": "/ws/predictions",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@router.get("/health")
def health_check():
    """
    헬스 체크

    서비스 상태 확인
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/status", response_model=ConnectionStatusResponse)
def get_status(connection_repo: ConnectionRepo):
    """
    연결 상태 조회

    WebSocket 연결 및 통계 정보 확인
    """
    stats = connection_repo.get_stats()
    return ConnectionStatusResponse(**stats)
