"""
Prediction Schemas

Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class PredictionRequest(BaseModel):
    """예측 요청 스키마 (DTO)"""
    type: str = Field(default="prediction", description="메시지 타입")
    detected_action: int = Field(..., ge=0, le=3, description="감지된 행동 ID (0-3)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0-1.0)")
    timestamp: float = Field(..., gt=0, description="타임스탬프")
    metadata: Optional[dict] = Field(None, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "prediction",
                "detected_action": 1,
                "confidence": 0.85,
                "timestamp": 1699876543.123,
                "metadata": {"source": "windows_client"}
            }
        }


class PredictionResponse(BaseModel):
    """예측 처리 응답 스키마"""
    status: str = Field(..., description="처리 상태 (success, error)")
    timestamp: float = Field(..., description="응답 타임스탬프")
    message: str = Field(..., description="응답 메시지")
    actions_taken: List[str] = Field(default_factory=list, description="수행된 액션 리스트")
    prediction_info: Optional[dict] = Field(None, description="예측 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "timestamp": 1699876543.456,
                "message": "Processed 2 actions",
                "actions_taken": ["speaker:alert", "phone:notify"],
                "prediction_info": {
                    "action": "행동 1 (높은 경고)",
                    "confidence": 0.85
                }
            }
        }


class ConnectionStatusResponse(BaseModel):
    """연결 상태 응답 스키마"""
    active_connections: int = Field(..., description="현재 활성 연결 수")
    total_messages: int = Field(..., description="총 처리 메시지 수")
    last_message_time: Optional[str] = Field(None, description="마지막 메시지 시간")
    is_connected: bool = Field(..., description="연결 여부")
    uptime: Optional[str] = Field(None, description="가동 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "active_connections": 1,
                "total_messages": 42,
                "last_message_time": "2024-11-01T21:30:00",
                "is_connected": True,
                "uptime": "02:15:30"
            }
        }
