"""
Phone Repository

안드로이드 핸드폰과의 데이터 접근 계층
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# API 서버 기본 URL
API_BASE_URL = "http://10.19.212.28:8080"


class PhoneRepository:
    """
    핸드폰 제어 Repository

    외부 시스템(Bluetooth Android)과의 데이터 접근 담당
    """

    def __init__(self, bluetooth_repo: Optional['BluetoothRepository'] = None):
        self.is_connected = False
        self.phone_address = None
        self.phone_name = None
        self.bluetooth_repo = bluetooth_repo

    async def connect(self, device_address: str, device_name: str = "Android Phone") -> bool:
        """
        안드로이드 기기 연결

        Args:
            device_address: 블루투스 기기 주소
            device_name: 블루투스 기기 이름

        Returns:
            bool: 연결 성공 여부
        """
        try:
            logger.info(f"Connecting to Android '{device_name}'...")

            if not self.bluetooth_repo:
                logger.warning("Bluetooth not available, using mock mode")
                self.is_connected = False
                return False

            success = self.bluetooth_repo.connect_device(device_address, device_name)

            if success:
                self.is_connected = True
                self.phone_address = device_address
                self.phone_name = device_name
                logger.info(f"Android '{device_name}' connected")
                return True
            else:
                logger.error("Android connection failed")
                return False

        except Exception as e:
            logger.error(f"Error connecting to Android: {e}")
            return False

    async def send_notification(self, value: float, predicted_class: int = None) -> bool:
        """
        알림 전송 - API 호출

        Args:
            value: 예측 신뢰도
            predicted_class: 예측 클래스

        Returns:
            bool: 전송 성공 여부
        """
        try:
            logger.info(f"Calling FCM send notification API - confidence: {value:.2f}, class: {predicted_class}")

            # FCM API 페이로드
            payload = {
                "user_id": "user4",
                "title": "Muhammad Ali",
                "body": "Impossible is just a big word thrown around by small men who find it easier to live in the world they've been given than to explore the power they have to change it. Impossible is not a fact. It's an opinion. Impossible is not a declaration. It's a dare. Impossible is potential. Impossible is temporary. Impossible is nothing."
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/fcm/send-to-user",
                    json=payload,
                    timeout=5.0
                )

                if response.status_code == 200:
                    logger.info(f"API call success: {response.json()}")
                    return True
                else:
                    logger.error(f"API call failed: {response.status_code}")
                    return False

        except httpx.RequestError as e:
            logger.error(f"Failed to call API: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    async def trigger_vibration(self, duration_ms: int = 200) -> bool:
        """
        진동 트리거

        Args:
            duration_ms: 진동 지속 시간

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.is_connected:
                logger.warning("Android not connected")
                return False

            logger.info(f"Triggering vibration ({duration_ms}ms)")

            # TODO: 실제 블루투스 진동 명령
            return True

        except Exception as e:
            logger.error(f"Failed to trigger vibration: {e}")
            return False

    async def send_custom_command(self, command: str, data: dict = None) -> bool:
        """
        커스텀 명령 전송

        Args:
            command: 명령 타입
            data: 추가 데이터

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.is_connected:
                logger.warning("Android not connected")
                return False

            logger.info(f"Sending custom command: {command}, data: {data}")

            # TODO: 실제 블루투스 커스텀 명령
            return True

        except Exception as e:
            logger.error(f"Failed to send custom command: {e}")
            return False

    async def disconnect(self) -> bool:
        """연결 해제"""
        try:
            if not self.is_connected:
                logger.info("No Android connected")
                return True

            logger.info(f"Disconnecting Android '{self.phone_name}'...")

            if self.bluetooth_repo and self.phone_address:
                success = self.bluetooth_repo.disconnect_device(self.phone_address, self.phone_name or "Unknown")

                if success:
                    self.is_connected = False
                    self.phone_address = None
                    self.phone_name = None
                    logger.info("Android disconnected")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

    def get_status(self) -> dict:
        """현재 연결 상태 반환"""
        return {
            "connected": self.is_connected,
            "device_address": self.phone_address,
            "device_name": self.phone_name
        }
