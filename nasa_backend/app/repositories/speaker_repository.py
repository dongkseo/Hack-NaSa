"""
Speaker Repository

블루투스 스피커와의 데이터 접근 계층
"""
import asyncio
import logging
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger(__name__)


class SpeakerRepository:
    """
    스피커 제어 Repository

    외부 시스템(Bluetooth)과의 데이터 접근 담당
    """

    def __init__(self):
        self.is_initialized = False
        self.device_address = None
        self.device_name = None
        # Lazy import to avoid errors if bluetooth module not available
        self._bt_manager = None

    def _get_bt_manager(self):
        """Bluetooth Manager lazy initialization"""
        if self._bt_manager is None:
            try:
                from bluetooth_universal_manager import BluetoothUniversalManager
                self._bt_manager = BluetoothUniversalManager()
            except ImportError:
                logger.warning("BluetoothUniversalManager not available")
                self._bt_manager = None
        return self._bt_manager

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
            bt_manager = self._get_bt_manager()
            if not bt_manager:
                logger.info("System media control mode (no Bluetooth)")
                self.is_initialized = True
                return True

            if device_address and device_name:
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    None,
                    bt_manager.connect_device,
                    device_address,
                    device_name
                )

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

    async def play_alert(self) -> bool:
        """경고음 재생"""
        try:
            logger.info("Playing alert sound")
            bt_manager = self._get_bt_manager()

            if bt_manager:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, bt_manager.media_play_pause)

            # TODO: 실제 경고음 파일 재생
            return True

        except Exception as e:
            logger.error(f"Failed to play alert: {e}")
            return False

    async def play_normal(self) -> bool:
        """일반 알림음 재생"""
        try:
            logger.info("Playing normal sound")
            bt_manager = self._get_bt_manager()

            if bt_manager:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, bt_manager.media_play_pause)

            return True

        except Exception as e:
            logger.error(f"Failed to play normal sound: {e}")
            return False

    async def stop(self) -> bool:
        """재생 중지"""
        try:
            logger.info("Stopping playback")
            bt_manager = self._get_bt_manager()

            if bt_manager:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, bt_manager.media_play_pause)

            return True

        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False

    async def disconnect(self) -> bool:
        """스피커 연결 해제"""
        try:
            logger.info("Disconnecting speaker")
            self.is_initialized = False
            self.device_address = None
            self.device_name = None
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False
