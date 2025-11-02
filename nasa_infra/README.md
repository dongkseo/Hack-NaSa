# NASA IoT Hub - FastAPI 3-Tier Architecture

> WiFi 센싱 기반 딥러닝 모델을 통한 실시간 IoT 기기 제어 시스템

## 🏗️ 아키텍처

이 프로젝트는 **FastAPI 3-Tier Architecture (Repository-Service Pattern)**를 따릅니다.

```
┌─────────────────────────────────────┐
│  API Layer (Presentation)           │  ← FastAPI 라우터, WebSocket
│  app/api/v1/endpoints/              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Service Layer (Business Logic)     │  ← 비즈니스 규칙, 조율
│  app/services/                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Repository Layer (Data Access)     │  ← Bluetooth, WebSocket 관리
│  app/repositories/                  │
└─────────────────────────────────────┘
```

### 레이어별 책임

| 레이어 | 디렉토리 | 책임 |
|--------|---------|------|
| **API** | `app/api/v1/endpoints/` | HTTP/WebSocket 엔드포인트, 요청/응답 처리 |
| **Service** | `app/services/` | 비즈니스 로직, Repository 조율 |
| **Repository** | `app/repositories/` | 외부 시스템 연동 (Bluetooth, WebSocket) |
| **Models** | `app/models/` | 도메인 모델 (비즈니스 엔티티) |
| **Schemas** | `app/schemas/` | Pydantic DTOs (요청/응답 스키마) |
| **Core** | `app/core/` | 설정, 의존성 주입 |

---

## 📁 프로젝트 구조

```
nasa_backend/
├── main.py                          # FastAPI 앱 진입점
├── requirements.txt                 # 의존성
├── .env                            # 환경 변수 (optional)
│
└── app/
    ├── api/                        # API Layer
    │   └── v1/
    │       ├── router.py          # API 라우터 통합
    │       └── endpoints/
    │           ├── health.py      # 헬스 체크
    │           └── predictions.py # 예측 WebSocket
    │
    ├── services/                   # Service Layer
    │   └── prediction_service.py  # 예측 비즈니스 로직
    │
    ├── repositories/               # Repository Layer
    │   ├── speaker_repository.py  # 스피커 Bluetooth
    │   ├── phone_repository.py    # 핸드폰 Bluetooth
    │   └── connection_repository.py # WebSocket 관리
    │
    ├── models/                     # Domain Models
    │   └── prediction.py          # 예측 엔티티
    │
    ├── schemas/                    # DTOs
    │   └── prediction.py          # 요청/응답 스키마
    │
    └── core/                       # Core
        ├── config.py              # 설정
        └── dependencies.py        # FastAPI DI
```

---

## 🚀 시작하기

### 1. 의존성 설치

```bash
cd nasa_backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택)

`.env` 파일 생성:

```env
# Application
APP_NAME="NASA IoT Hub"
APP_VERSION="2.0.0"
LOG_LEVEL="INFO"

# Business Logic
CONFIDENCE_THRESHOLD=0.5

# Bluetooth (optional)
SPEAKER_ADDRESS="XX:XX:XX:XX:XX:XX"
SPEAKER_NAME="My Speaker"
PHONE_ADDRESS="YY:YY:YY:YY:YY:YY"
PHONE_NAME="My Phone"
```

### 3. 서버 실행

```bash
# 개발 모드 (auto-reload)
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 📡 API 엔드포인트

### REST API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | API 문서로 리다이렉트 |
| GET | `/api/v1/` | API 정보 |
| GET | `/api/v1/health` | 헬스 체크 |
| GET | `/api/v1/status` | 연결 상태 조회 |

### WebSocket

| Endpoint | 설명 |
|----------|------|
| `/api/v1/predictions/ws/predictions` | 예측 결과 실시간 처리 |

---

## 🔌 WebSocket 프로토콜

### Client → Server (예측 요청)

```json
{
  "type": "prediction",
  "detected_action": 1,
  "confidence": 0.85,
  "timestamp": 1699876543.123,
  "metadata": {
    "source": "windows_client"
  }
}
```

### Server → Client (처리 결과)

```json
{
  "status": "success",
  "timestamp": 1699876543.456,
  "message": "Processed 2 actions",
  "actions_taken": [
    "speaker:play_alert",
    "phone:notify"
  ],
  "prediction_info": {
    "action": "행동 1 (높은 경고)",
    "confidence": 0.85
  }
}
```

---

## 🎯 비즈니스 규칙

### 행동 감지 매핑

| Action ID | 이름 | 스피커 | 핸드폰 | 설명 |
|-----------|------|--------|--------|------|
| 0 | 감지 없음 | - | - | 아무 동작 안함 |
| 1 | 행동 1 | 경고음 | 알림 | 높은 경고 |
| 2 | 행동 2 | 일반음 | 알림 | 중간 알림 |
| 3 | 행동 3 | - | 알림 | 약한 알림 |

### 신뢰도 임계값

- 기본값: `0.5` (50%)
- 신뢰도가 임계값 미만이면 액션 실행 안 함
- 설정 변경: 환경 변수 `CONFIDENCE_THRESHOLD`

---

## 🧪 테스트

### WebSocket 테스트 클라이언트

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/predictions/ws/predictions"
    async with websockets.connect(uri) as websocket:
        # 예측 요청 전송
        request = {
            "type": "prediction",
            "detected_action": 1,
            "confidence": 0.85,
            "timestamp": 1699876543.123
        }
        await websocket.send(json.dumps(request))

        # 응답 수신
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_websocket())
```

---

## 🛠️ 개발 가이드

### FastAPI Dependency Injection 사용

```python
from fastapi import Depends
from app.core.dependencies import PredictionSvc

@router.get("/example")
def example_endpoint(service: PredictionSvc):
    # service는 자동으로 주입됨
    return service.get_stats()
```

### 새로운 엔드포인트 추가

1. `app/api/v1/endpoints/` 에 새 파일 생성
2. `app/api/v1/router.py` 에 라우터 추가

```python
# app/api/v1/router.py
from app.api.v1.endpoints import new_endpoint

api_router.include_router(
    new_endpoint.router,
    prefix="/new",
    tags=["New"]
)
```

### 새로운 비즈니스 로직 추가

1. `app/services/` 에 서비스 생성
2. `app/core/dependencies.py` 에 의존성 추가
3. API 엔드포인트에서 `Depends()` 사용

---

## 📦 Dependencies

- **FastAPI**: 웹 프레임워크
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버
- **WebSockets**: WebSocket 지원
- **pydantic-settings**: 환경 변수 관리

---

## 🔄 마이그레이션 가이드 (기존 코드에서)

기존 Clean Architecture에서 마이그레이션:

| Before (Clean Arch) | After (3-Tier) |
|---------------------|----------------|
| `presentation/` | `api/v1/endpoints/` |
| `application/` + `domain/services/` | `services/` |
| `domain/entities/` | `models/` |
| `infrastructure/` | `repositories/` |
| `container.py` | `core/dependencies.py` |

---

## 📝 License

MIT License

---

## 👥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Contact

Project Link: [https://github.com/yourusername/nasa-iot-hub](https://github.com/yourusername/nasa-iot-hub)
