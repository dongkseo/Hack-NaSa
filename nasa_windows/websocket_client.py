"""
Windows WiFi 센싱 WebSocket 클라이언트

WiFi 신호 기반 딥러닝 행동 감지 결과를 MacBook 허브로 전송
"""
import sys
import io

# Windows 터미널 한글 깨짐 방지
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import websockets
import json
import time
from typing import Optional


class WiFiSensingClient:
    """WiFi 센싱 WebSocket 클라이언트"""

    def __init__(self, server_uri: str):
        """
        Args:
            server_uri: MacBook 허브 WebSocket URI
                       예: "ws://192.168.0.10:8000/ws/windows"
        """
        self.server_uri = server_uri
        self.is_connected = False
        self.websocket = None

    async def connect(self):
        """MacBook 허브에 연결"""
        try:
            print(f"🔗 MacBook 허브 연결 시도: {self.server_uri}")
            self.websocket = await websockets.connect(self.server_uri)
            self.is_connected = True
            print("✅ MacBook 허브 연결 성공")
            return True

        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            self.is_connected = False
            return False

    async def send_detection(
        self,
        detected_action: int,
        confidence: float,
        metadata: dict = None
    ):
        """
        행동 감지 결과 전송

        Args:
            detected_action: 감지된 행동 ID
                           0: 감지 없음
                           1: 행동 1
                           2: 행동 2
                           3: 행동 3
            confidence: 신뢰도 (0.0 ~ 1.0)
            metadata: 추가 메타데이터 (선택)
        """
        if not self.is_connected or not self.websocket:
            print("⚠️ 허브에 연결되지 않음")
            return False

        try:
            message = {
                "type": "prediction",
                "detected_action": detected_action,
                "confidence": confidence,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }

            # MacBook 허브로 전송
            await self.websocket.send(json.dumps(message))
            print(f"📤 전송: 행동 ID={detected_action}, 신뢰도={confidence:.2%}")

            # 응답 수신
            response = await self.websocket.recv()
            response_data = json.loads(response)
            print(f"📥 응답: {response_data.get('message', 'OK')}")

            return True

        except Exception as e:
            print(f"❌ 전송 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """연결 종료"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("🔌 연결 종료")

    async def run_with_model(self, model_predict_fn, interval: float = 0.05):
        """
        실제 딥러닝 모델과 함께 실행

        Args:
            model_predict_fn: 예측 함수
                            반환 형식: (detected_action: int, confidence: float)
            interval: 예측 주기 (초) - 기본 0.05초 (20Hz)
        """
        if not await self.connect():
            return

        try:
            print(f"\n🚀 WiFi 센싱 시작 (주기: {interval}초)")
            print("Ctrl+C로 종료\n")

            while True:
                # TODO: 실제 WiFi 데이터 수집
                # wifi_data = collect_wifi_signal()

                # 딥러닝 모델 예측
                detected_action, confidence = model_predict_fn()

                # MacBook 허브로 전송
                await self.send_detection(detected_action, confidence)

                # 대기
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹️ 사용자 중단")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        finally:
            await self.disconnect()


async def main():
    """메인 함수 - 테스트/데모용"""

    # MacBook IP 주소로 변경 필요
    MACBOOK_IP = "localhost"  # 또는 "192.168.0.10"
    MACBOOK_PORT = 8000

    server_uri = f"ws://{MACBOOK_IP}:{MACBOOK_PORT}/ws/windows"

    client = WiFiSensingClient(server_uri)

    # 더미 예측 함수 (실제 모델로 교체 필요)
    def dummy_model_predict():
        """랜덤 행동 감지 결과 생성 (테스트용)"""
        import random

        # 랜덤 행동 ID (0~3)
        detected_action = random.randint(0, 3)

        # 랜덤 신뢰도
        confidence = random.uniform(0.3, 0.95)

        return detected_action, confidence

    # 실행
    await client.run_with_model(
        model_predict_fn=dummy_model_predict,
        interval=1.0  # 1초마다 (테스트용)
    )


if __name__ == "__main__":
    print("=" * 80)
    print("🖥️  Windows WiFi 센싱 클라이언트")
    print("=" * 80)

    asyncio.run(main())