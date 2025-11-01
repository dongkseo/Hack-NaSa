"""
테스트용 더미 데이터 전송 스크립트

MacBook 허브와의 WebSocket 연결을 테스트하기 위한 간단한 클라이언트
다양한 시나리오의 행동 감지 결과를 전송
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


async def send_test_detection(uri: str, detected_action: int, confidence: float, description: str):
    """테스트 행동 감지 결과 전송"""
    try:
        async with websockets.connect(uri) as websocket:
            message = {
                "type": "prediction",
                "detected_action": detected_action,
                "confidence": confidence,
                "timestamp": time.time(),
                "metadata": {"test": description}
            }

            print(f"\n📤 전송: {description}")
            print(f"   행동 ID: {detected_action}, 신뢰도: {confidence:.2%}")

            await websocket.send(json.dumps(message))

            response = await websocket.recv()
            response_data = json.loads(response)

            print(f"✅ 응답: {response_data.get('status')}")
            print(f"   메시지: {response_data.get('message')}")

            return True

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


async def run_test_scenarios(macbook_ip: str = "localhost", port: int = 8000):
    """다양한 테스트 시나리오 실행"""

    uri = f"ws://{macbook_ip}:{port}/ws/windows"

    print("=" * 80)
    print("🧪 WebSocket 테스트 시나리오")
    print("=" * 80)

    # 시나리오 1: 행동 1 감지 (높은 신뢰도) - 경고음 + 알림
    await send_test_detection(
        uri, 1, 0.95,
        "행동 1 감지 (95% 신뢰도) - 경고음 + 알림 예상"
    )
    await asyncio.sleep(2)

    # 시나리오 2: 행동 2 감지 (높은 신뢰도) - 일반음 + 알림
    await send_test_detection(
        uri, 2, 0.85,
        "행동 2 감지 (85% 신뢰도) - 일반음 + 알림 예상"
    )
    await asyncio.sleep(2)

    # 시나리오 3: 행동 3 감지 (높은 신뢰도) - 알림만
    await send_test_detection(
        uri, 3, 0.75,
        "행동 3 감지 (75% 신뢰도) - 알림만 예상"
    )
    await asyncio.sleep(2)

    # 시나리오 4: 행동 1 감지 (낮은 신뢰도) - 무시
    await send_test_detection(
        uri, 1, 0.40,
        "행동 1 감지 (40% 신뢰도) - 낮은 신뢰도로 무시 예상"
    )
    await asyncio.sleep(2)

    # 시나리오 5: 감지 없음 (높은 신뢰도)
    await send_test_detection(
        uri, 0, 0.90,
        "감지 없음 (90% 신뢰도) - 아무 동작 안함"
    )

    print("\n" + "=" * 80)
    print("✅ 모든 테스트 시나리오 완료")
    print("=" * 80)


async def run_continuous_test(
    macbook_ip: str = "localhost",
    port: int = 8000,
    interval: float = 1.0,
    count: int = 10
):
    """연속 테스트"""

    uri = f"ws://{macbook_ip}:{port}/ws/windows"

    print("=" * 80)
    print(f"🔄 연속 테스트 ({count}회, {interval}초 간격)")
    print("=" * 80)

    import random

    action_names = {
        0: "감지 없음",
        1: "행동 1",
        2: "행동 2",
        3: "행동 3"
    }

    for i in range(count):
        # 랜덤 행동 ID와 신뢰도 생성
        detected_action = random.randint(0, 3)
        confidence = random.uniform(0.3, 0.95)

        await send_test_detection(
            uri,
            detected_action,
            confidence,
            f"테스트 {i+1}/{count} - {action_names[detected_action]}"
        )

        if i < count - 1:
            await asyncio.sleep(interval)

    print("\n" + "=" * 80)
    print("✅ 연속 테스트 완료")
    print("=" * 80)


async def run_action_test(macbook_ip: str = "localhost", port: int = 8000):
    """각 행동별 테스트"""

    uri = f"ws://{macbook_ip}:{port}/ws/windows"

    print("=" * 80)
    print("🎬 행동별 테스트")
    print("=" * 80)

    actions = [
        (0, 0.90, "감지 없음 - 아무 동작 안함"),
        (1, 0.90, "행동 1 - 경고음 + 알림"),
        (2, 0.90, "행동 2 - 일반음 + 알림"),
        (3, 0.90, "행동 3 - 알림만")
    ]

    for action_id, conf, desc in actions:
        await send_test_detection(uri, action_id, conf, desc)
        await asyncio.sleep(3)

    print("\n" + "=" * 80)
    print("✅ 행동별 테스트 완료")
    print("=" * 80)


async def main():
    """메인 함수"""

    # MacBook IP 설정 (필요시 수정)
    MACBOOK_IP = input("MacBook IP 주소 입력 (기본: localhost): ").strip() or "localhost"
    MACBOOK_PORT = 8000

    print(f"\n연결 대상: ws://{MACBOOK_IP}:{MACBOOK_PORT}/ws/windows\n")

    # 테스트 모드 선택
    print("테스트 모드 선택:")
    print("1. 시나리오 테스트 (5가지 시나리오)")
    print("2. 연속 테스트 (10회 랜덤 전송)")
    print("3. 행동별 테스트 (각 행동 1회씩)")
    print("4. 단일 테스트 (1회만 전송)")

    choice = input("\n선택 (1/2/3/4): ").strip()

    if choice == "1":
        await run_test_scenarios(MACBOOK_IP, MACBOOK_PORT)

    elif choice == "2":
        count = input("전송 횟수 (기본: 10): ").strip()
        count = int(count) if count.isdigit() else 10

        interval = input("전송 간격 (초, 기본: 1.0): ").strip()
        interval = float(interval) if interval else 1.0

        await run_continuous_test(MACBOOK_IP, MACBOOK_PORT, interval, count)

    elif choice == "3":
        await run_action_test(MACBOOK_IP, MACBOOK_PORT)

    elif choice == "4":
        print("\n행동 ID 선택:")
        print("  0: 감지 없음")
        print("  1: 행동 1 (경고음 + 알림)")
        print("  2: 행동 2 (일반음 + 알림)")
        print("  3: 행동 3 (알림만)")

        action_id = input("행동 ID 입력 (0-3): ").strip()
        confidence = input("신뢰도 입력 (0.0-1.0, 예: 0.85): ").strip()

        try:
            action_id = int(action_id)
            confidence = float(confidence)

            if 0 <= action_id <= 3 and 0.0 <= confidence <= 1.0:
                await send_test_detection(
                    f"ws://{MACBOOK_IP}:{MACBOOK_PORT}/ws/windows",
                    action_id,
                    confidence,
                    "사용자 입력 테스트"
                )
            else:
                print("❌ 잘못된 범위")
        except:
            print("❌ 잘못된 입력 형식")

    else:
        print("❌ 잘못된 선택")


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 NASA IoT Hub - 테스트 클라이언트")
    print("=" * 80)
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자 중단")