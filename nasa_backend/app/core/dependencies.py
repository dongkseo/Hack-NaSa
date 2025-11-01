"""
FastAPI Dependencies

Dependency injection providers using FastAPI's Depends system
"""
from typing import Annotated
from fastapi import Depends
from app.repositories.speaker_repository import SpeakerRepository
from app.repositories.phone_repository import PhoneRepository
from app.repositories.connection_repository import ConnectionRepository
from app.services.prediction_service import PredictionService


# Repository instances (singleton-like)
_speaker_repo = SpeakerRepository()
_phone_repo = PhoneRepository()
_connection_repo = ConnectionRepository()


# Repository Dependencies
def get_speaker_repository() -> SpeakerRepository:
    """스피커 Repository 의존성"""
    return _speaker_repo


def get_phone_repository() -> PhoneRepository:
    """핸드폰 Repository 의존성"""
    return _phone_repo


def get_connection_repository() -> ConnectionRepository:
    """연결 Repository 의존성"""
    return _connection_repo


# Service Dependencies
def get_prediction_service(
    speaker_repo: Annotated[SpeakerRepository, Depends(get_speaker_repository)],
    phone_repo: Annotated[PhoneRepository, Depends(get_phone_repository)],
    connection_repo: Annotated[ConnectionRepository, Depends(get_connection_repository)]
) -> PredictionService:
    """예측 서비스 의존성"""
    return PredictionService(
        speaker_repo=speaker_repo,
        phone_repo=phone_repo,
        connection_repo=connection_repo,
        confidence_threshold=0.5
    )


# Type Aliases for cleaner code
SpeakerRepo = Annotated[SpeakerRepository, Depends(get_speaker_repository)]
PhoneRepo = Annotated[PhoneRepository, Depends(get_phone_repository)]
ConnectionRepo = Annotated[ConnectionRepository, Depends(get_connection_repository)]
PredictionSvc = Annotated[PredictionService, Depends(get_prediction_service)]
