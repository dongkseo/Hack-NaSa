# NASA Windows Client

Windows WiFi 센싱 딥러닝 클라이언트

## 📋 파일 구조

```
nasa_windows/
├── websocket_client.py    # 실제 WiFi 센싱 클라이언트
├── test_sender.py          # 테스트용 더미 데이터 전송 스크립트
├── requirements.txt        # Python 의존성
└── README.md              # 이 파일
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. MacBook 허브 IP 확인

MacBook 터미널에서:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

예시 출력: `192.168.0.10`

### 3. 테스트 실행

```bash
# 테스트 클라이언트 실행
python test_sender.py
```

MacBook IP를 입력하고 원하는 테스트 모드 선택:
- **1번**: 시나리오 테스트 (5가지 신뢰도 시나리오)
- **2번**: 연속 테스트 (랜덤 데이터 반복 전송)
- **3번**: 단일 테스트 (수동 입력)

### 4. 실제 모델과 함께 실행

```python
# websocket_client.py 수정 필요

# 1. MacBook IP 설정
MACBOOK_IP = "192.168.0.10"  # 실제 IP로 변경

# 2. 모델 예측 함수 교체
def your_model_predict():
    # WiFi 데이터 수집
    wifi_data = collect_wifi_signal()

    # 딥러닝 모델 예측
    prediction = model(wifi_data)

    return prediction.tolist()

# 3. 실행
client.run_with_model(
    model_predict_fn=your_model_predict,
    interval=0.05  # 20Hz
)
```

## 📡 메시지 형식

### Windows → MacBook

```json
{
  "type": "prediction",
  "result": [0.85, 0.12, 0.03],
  "timestamp": 1730419200.123,
  "metadata": {}
}
```

### MacBook → Windows

```json
{
  "status": "processed",
  "timestamp": 1730419200.456,
  "message": "Actions: speaker:alert, phone:notify"
}
```

## 🧪 테스트 시나리오

### 시나리오 1: 높은 신뢰도 (95%)
- 예측: `[0.95, 0.03, 0.02]`
- 예상 동작: 경고음 + 핸드폰 알림

### 시나리오 2: 중간 신뢰도 (65%)
- 예측: `[0.65, 0.25, 0.10]`
- 예상 동작: 일반음 + 핸드폰 알림

### 시나리오 3: 낮은 신뢰도 (40%)
- 예측: `[0.40, 0.35, 0.25]`
- 예상 동작: 핸드폰 알림만

### 시나리오 4: 매우 낮은 신뢰도 (25%)
- 예측: `[0.25, 0.40, 0.35]`
- 예상 동작: 무시

## 🔧 커스터마이징

### 전송 주기 변경

```python
await client.run_with_model(
    model_predict_fn=your_predict_fn,
    interval=0.1  # 10Hz (0.1초마다)
)
```

### 메타데이터 추가

```python
await client.send_prediction(
    prediction_result=[0.85, 0.12, 0.03],
    metadata={
        "model_version": "v1.2",
        "device_id": "windows-001",
        "location": "lab"
    }
)
```

## ⚠️ 주의사항

- MacBook 허브가 먼저 실행되어 있어야 함
- 같은 WiFi 네트워크에 연결되어 있어야 함
- 방화벽 설정 확인 필요

## 📝 예제

```python
import asyncio
from websocket_client import WiFiSensingClient

async def main():
    # 클라이언트 생성
    client = WiFiSensingClient("ws://192.168.0.10:8000/ws/windows")

    # 연결
    if await client.connect():
        # 단일 예측 전송
        await client.send_prediction([0.85, 0.12, 0.03])

        # 연결 종료
        await client.disconnect()

asyncio.run(main())
```
