"""
Speaker Repository

블루투스 스피커와의 데이터 접근 계층
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpeakerRepository:
    """
    스피커 제어 Repository

    외부 시스템(Bluetooth)과의 데이터 접근 담당
    """

    def __init__(self, bluetooth_repo: Optional['BluetoothRepository'] = None):
        self.is_initialized = False
        self.device_address = None
        self.device_name = None
        self.bluetooth_repo = bluetooth_repo

    async def initialize(self, device_address: str = None, device_name: str = None) -> bool:
        """
        스피커 초기화

        Args:
            device_address: 블루투스 기기 주소
            device_name: 블루투스 기기 이름

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.bluetooth_repo:
                logger.info("System media control mode (no Bluetooth)")
                self.is_initialized = True
                return True

            if device_address and device_name:
                success = self.bluetooth_repo.connect_device(device_address, device_name)

                if success:
                    self.device_address = device_address
                    self.device_name = device_name
                    logger.info(f"Speaker '{device_name}' connected")
                else:
                    logger.warning("Speaker connection failed, using system default")

                self.is_initialized = True
            else:
                logger.info("System media control mode")
                self.is_initialized = True

            return True

        except Exception as e:
            logger.error(f"Failed to initialize speaker: {e}")
            self.is_initialized = False
            return False

    async def media_play_pause(self) -> bool:
        """재생/일시정지"""
        try:
            logger.info("Playing alert sound")

            if self.bluetooth_repo:
                self.bluetooth_repo.media_play_pause()

            # TODO: 실제 경고음 파일 재생
            return True

        except Exception as e:
            logger.error(f"Failed to play alert: {e}")
            return False

    async def play_normal(self) -> bool:
        """일반 알림음 재생"""
        try:
            logger.info("Playing normal sound")

            if self.bluetooth_repo:
                self.bluetooth_repo.media_play_pause()

            return True

        except Exception as e:
            logger.error(f"Failed to play normal sound: {e}")
            return False

    async def stop(self) -> bool:
        """재생 중지"""
        try:
            logger.info("Stopping playback")

            if self.bluetooth_repo:
                self.bluetooth_repo.media_play_pause()

            return True

        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False

    async def disconnect(self) -> bool:
        """스피커 연결 해제"""
        try:
            logger.info("Disconnecting speaker")

            if self.bluetooth_repo and self.device_address:
                self.bluetooth_repo.disconnect_device(self.device_address, self.device_name or "Unknown")

            self.is_initialized = False
            self.device_address = None
            self.device_name = None
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False
