"""
Prediction Domain Model

비즈니스 엔티티: 행동 예측 결과
"""
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class ActionType(IntEnum):
    """감지된 행동 타입"""
    NONE = 0
    ACTION_1 = 1
    ACTION_2 = 2
    ACTION_3 = 3

    @property
    def description(self) -> str:
        """행동 설명"""
        descriptions = {
            self.NONE: "감지 없음",
            self.ACTION_1: "행동 1",
            self.ACTION_2: "행동 2",
            self.ACTION_3: "행동 3"
        }
        return descriptions.get(self, "알 수 없음")


@dataclass
class Prediction:
    """
    예측 결과 도메인 모델

    비즈니스 규칙:
    - detected_action은 0-3 범위
    - confidence는 0.0-1.0 범위
    """
    detected_action: int
    confidence: float
    timestamp: float
    metadata: Optional[dict] = None

    def __post_init__(self):
        """생성 후 검증"""
        if not 0 <= self.detected_action <= 3:
            raise ValueError(f"Invalid detected_action: {self.detected_action}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}")
        if self.timestamp <= 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")

    @property
    def action_type(self) -> ActionType:
        """행동 타입 enum 반환"""
        return ActionType(self.detected_action)

    @property
    def action_name(self) -> str:
        """행동 이름 반환"""
        return self.action_type.description

    def is_confident(self, threshold: float = 0.5) -> bool:
        """신뢰도가 임계값 이상인지 확인"""
        return self.confidence >= threshold
