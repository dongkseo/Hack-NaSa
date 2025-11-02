"""
Prediction Service

예측 처리 비즈니스 로직을 담당하는 서비스
"""
import logging
from typing import List, Dict
from app.models.prediction import Prediction, ActionType
from app.repositories.speaker_repository import SpeakerRepository
from app.repositories.phone_repository import PhoneRepository
from app.repositories.connection_repository import ConnectionRepository

logger = logging.getLogger(__name__)


class PredictionService:
    """
    예측 처리 서비스

    책임:
    - 예측 결과 검증
    - 비즈니스 규칙 적용 (신뢰도 체크, 액션 결정)
    - Repository를 통한 IoT 제어 실행
    """

    def __init__(
        self,
        speaker_repo: SpeakerRepository,
        phone_repo: PhoneRepository,
        connection_repo: ConnectionRepository,
        confidence_threshold: float = 0.5
    ):
        """
        Args:
            speaker_repo: 스피커 Repository
            phone_repo: 핸드폰 Repository
            connection_repo: 연결 Repository
            confidence_threshold: 신뢰도 임계값
        """
        self.speaker_repo = speaker_repo
        self.phone_repo = phone_repo
        self.connection_repo = connection_repo
        self.confidence_threshold = confidence_threshold

        # 행동별 액션 매핑 설정
        self.action_mappings = self._initialize_action_mappings()

    def _initialize_action_mappings(self) -> Dict[int, Dict]:
        """행동 ID별 액션 매핑 초기화"""
        return {
            0: {  # 감지 없음
                "speaker": None,
                "phone": None,
                "description": "아무 동작 안함"
            },
            1: {  # 행동 1 - wave
                "speaker": "media_play_pause",
                "phone": "notify",
                "description": "재생/일시정지"
            },
            2: {  # 행동 2 - 
                "speaker": "media_next",
                "phone": "notify",
                "description": "다음 트랙"
            },
            3: {  # 행동 3 - 
                "speaker": None,
                "phone": "notify",
                "description": "알림만"
            }
        }

    async def process_prediction(
        self,
        detected_action: int,
        confidence: float,
        timestamp: float,
        metadata: dict = None
    ) -> Dict:
        """
        예측 결과 처리

        Args:
            detected_action: 감지된 행동 ID (0-3)
            confidence: 신뢰도 (0.0-1.0)
            timestamp: 타임스탬프
            metadata: 추가 메타데이터

        Returns:
            dict: 처리 결과
        """
        try:
            # 1. 도메인 모델 생성 (자동 검증)
            prediction = Prediction(
                detected_action=detected_action,
                confidence=confidence,
                timestamp=timestamp,
                metadata=metadata
            )

            logger.info(
                f"Processing prediction: {prediction.action_name} "
                f"(confidence: {prediction.confidence:.2%})"
            )

            # 2. 통계 업데이트
            self.connection_repo.update_stats()

            # 3. 비즈니스 규칙 적용: 신뢰도 체크
            if not prediction.is_confident(self.confidence_threshold):
                logger.info(
                    f"Low confidence ({prediction.confidence:.2%} < {self.confidence_threshold:.2%}), ignoring"
                )
                return {
                    "status": "success",
                    "message": "Low confidence, no action taken",
                    "actions_taken": [],
                    "prediction_info": {
                        "action": prediction.action_name,
                        "confidence": prediction.confidence
                    }
                }

            # 4. 액션 결정 및 실행
            actions_taken = await self._execute_actions(prediction)

            # 5. 결과 반환
            return {
                "status": "success",
                "message": f"Processed {len(actions_taken)} actions",
                "actions_taken": actions_taken,
                "prediction_info": {
                    "action": prediction.action_name,
                    "confidence": prediction.confidence
                }
            }

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                "status": "error",
                "message": "Invalid input",
                "actions_taken": []
            }

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {
                "status": "error",
                "message": "An error occurred",
                "actions_taken": []
            }

    async def _execute_actions(self, prediction: Prediction) -> List[str]:
        """
        액션 실행

        Args:
            prediction: 예측 도메인 모델

        Returns:
            List[str]: 실행된 액션 리스트
        """
        actions_taken = []

        # 매핑 조회
        if prediction.detected_action not in self.action_mappings:
            logger.warning(f"Unknown action ID: {prediction.detected_action}")
            return actions_taken

        mapping = self.action_mappings[prediction.detected_action]
        logger.info(f"Action mapping: {mapping['description']}")

        # 1. 스피커 제어
        speaker_action = mapping.get("speaker")
        if speaker_action:
            success = await self._execute_speaker_action(speaker_action)
            if success:
                actions_taken.append(f"speaker:{speaker_action}")

        # 2. 핸드폰 제어
        phone_action = mapping.get("phone")
        if phone_action:
            success = await self._execute_phone_action(
                phone_action,
                prediction.confidence,
                prediction.detected_action
            )
            if success:
                actions_taken.append(f"phone:{phone_action}")

        return actions_taken

    async def _execute_speaker_action(self, action: str) -> bool:
        """
        스피커 액션 실행

        Args:
            action: 액션 타입 ("media_play_pause", "media_next", "stop")

        Returns:
            bool: 실행 성공 여부
        """
        try:
            if action == "media_play_pause":
                return await self.speaker_repo.media_play_pause()
            elif action == "media_next":
                return await self.speaker_repo.media_next()
            elif action == "stop":
                return await self.speaker_repo.stop()
            return False

        except Exception as e:
            logger.error(f"Speaker action failed: {e}")
            return False

    async def _execute_phone_action(
        self,
        action: str,
        confidence: float,
        predicted_class: int
    ) -> bool:
        """
        핸드폰 액션 실행

        Args:
            action: 액션 타입 ("notify", "vibrate", "custom")
            confidence: 신뢰도
            predicted_class: 예측 클래스

        Returns:
            bool: 실행 성공 여부
        """
        try:
            if action == "notify":
                return await self.phone_repo.send_notification(
                    value=confidence,
                    predicted_class=predicted_class
                )
            elif action == "vibrate":
                return await self.phone_repo.trigger_vibration()
            elif action == "custom":
                return await self.phone_repo.send_custom_command(
                    command="custom",
                    data={"confidence": confidence, "class": predicted_class}
                )
            return False

        except Exception as e:
            logger.error(f"Phone action failed: {e}")
            return False

    def update_confidence_threshold(self, threshold: float) -> None:
        """
        신뢰도 임계값 업데이트

        Args:
            threshold: 새로운 임계값 (0.0-1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold updated to {threshold:.2%}")

    def get_action_mapping(self, action_id: int) -> dict:
        """
        특정 행동 ID의 매핑 정보 조회

        Args:
            action_id: 행동 ID

        Returns:
            dict: 매핑 정보
        """
        if action_id not in self.action_mappings:
            raise ValueError(f"Invalid action_id: {action_id}")

        return self.action_mappings[action_id].copy()
