"""
NASA IoT Hub - FastAPI 메인 애플리케이션

FastAPI 3-Tier Architecture (Repository-Service Pattern)

구조:
┌─────────────────────────────────────┐
│  API Layer (Presentation)           │  ← FastAPI 라우터
│  - app/api/v1/endpoints/            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Service Layer (Business Logic)     │  ← 비즈니스 로직
│  - app/services/                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Repository Layer (Data Access)     │  ← 외부 시스템 연동
│  - app/repositories/                │
└─────────────────────────────────────┘
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.v1.router import api_router
from app.core.config import settings

# 로깅 설정
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리

    시작 시: 초기화 작업
    종료 시: 리소스 정리
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # TODO: Bluetooth 기기 초기화 (필요 시)
    # from app.core.dependencies import _speaker_repo, _phone_repo
    # if settings.SPEAKER_ADDRESS:
    #     await _speaker_repo.initialize(settings.SPEAKER_ADDRESS, settings.SPEAKER_NAME)
    # if settings.PHONE_ADDRESS:
    #     await _phone_repo.connect(settings.PHONE_ADDRESS, settings.PHONE_NAME)

    logger.info("Application started successfully")

    yield

    # 종료 시 리소스 정리
    logger.info("Shutting down application...")
    # TODO: 연결 해제
    # await _speaker_repo.disconnect()
    # await _phone_repo.disconnect()


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# API v1 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """루트 경로를 API 문서로 리다이렉트"""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )