# NaSa Mobile - 블루투스 신호 처리 앱

블루투스를 통해 수신된 신호를 실시간으로 처리하고 적절한 액션을 취하는 Flutter 앱입니다.

## 🚀 주요 기능

### 📱 블루투스 연결 관리
- BLE Peripheral 모드로 다른 기기의 연결 대기
- 실시간 연결 상태 모니터링
- 연결된 디바이스 정보 표시

### 🔔 지능형 신호 처리
- 다양한 신호 타입 자동 인식 (알람, 알림, 진동, 사운드 등)
- 우선순위 기반 신호 처리
- 규칙 기반 액션 실행 시스템
- 야간 모드 지원

### 📊 통계 및 모니터링
- 실시간 신호 통계
- 성능 메트릭 추적
- 처리 로그 및 히스토리
- 신호 처리 성공률 분석

### ⚙️ 유연한 설정
- 신호별 액션 규칙 커스터마이징
- 시간대별 다른 처리 규칙
- 디바이스별 필터링
- 조건부 액션 실행

## 🏗️ 프로젝트 구조

```
lib/
├── core/
│   ├── enums/           # 열거형 정의
│   │   ├── bluetooth_enum.dart
│   │   └── signal_enum.dart
│   ├── models/          # 데이터 모델
│   │   ├── device_model.dart
│   │   ├── signal_model.dart
│   │   ├── signal_processing_model.dart
│   │   └── statistics_model.dart
│   └── services/        # 비즈니스 로직
│       ├── bluetooth_signal_service.dart
│       └── local_notification_service.dart
├── data/               # 데이터 레이어
├── presentation/       # UI 레이어
│   ├── view_models/
│   │   └── enhanced_action_view_model.dart
│   └── views/
│       └── enhanced_home.dart
└── main.dart
```

## 📋 모델 구조

### 핵심 모델들

#### 1. BluetoothDevice
연결된 블루투스 디바이스 정보
```dart
class BluetoothDevice {
  final String id;
  final String name;
  final DateTime connectedAt;
  final int rssi; // 신호 강도
}
```

#### 2. BluetoothSignal
수신된 신호 데이터
```dart
class BluetoothSignal {
  final SignalType type;        // 신호 타입
  final String rawData;         // 원시 데이터
  final Map<String, dynamic>? payload; // 파싱된 데이터
  final int priority;           // 우선순위 (1: 긴급 ~ 4: 낮음)
}
```

#### 3. SignalProcessingRule
신호 처리 규칙
```dart
class SignalProcessingRule {
  final SignalType signalType;
  final List<SignalActionType> actions;
  final Map<String, dynamic>? conditions;
  final int priority;
}
```

### 신호 타입 (SignalType)
- `alarm`: 긴급 알람
- `notification`: 일반 알림
- `vibration`: 진동 요청
- `sound`: 사운드 재생
- `status`: 상태 확인
- `data`: 일반 데이터

### 액션 타입 (SignalActionType)
- `playSound`: 사운드 재생
- `vibrate`: 진동
- `showNotification`: 알림 표시
- `displayMessage`: 메시지 표시
- `logData`: 데이터 로깅
- `sendResponse`: 응답 전송

## 🔧 사용 방법

### 1. 신호 처리 예시
```dart
// 신호 생성
final signal = BluetoothSignal.fromRawData(
  rawData: "ALARM;priority=1;message=Emergency",
  deviceId: "macbook_001",
);

// 자동 처리
await signalService.processSignal(signal);
```

### 2. 커스텀 규칙 추가
```dart
final customRule = SignalProcessingRule(
  id: 'custom_night_alarm',
  signalType: SignalType.alarm,
  actions: [SignalActionType.vibrate, SignalActionType.showNotification],
  conditions: {
    'timeRange': {'startHour': 22, 'endHour': 7},
  },
  priority: 1,
);

config.addRule(customRule);
```

### 3. 통계 확인
```dart
final stats = signalService.generateStatistics(
  startDate: DateTime.now().subtract(Duration(hours: 24)),
);

print('총 신호: ${stats.totalSignals}');
print('시간당 평균: ${stats.averageSignalsPerHour}');
```

## 📦 의존성

- `flutter_ble_peripheral`: BLE Peripheral 기능
- `audioplayers`: 사운드 재생
- `provider`: 상태 관리
- `flutter_dotenv`: 환경 변수 관리
- `flutter_foreground_task`: 백그라운드 작업

## ⚙️ 설정

### 환경 변수 (.env)
```properties
SERVICE_UUID=8F605319-9B6B-EF59-93E3-E4A8B2FBBE89
CHARACTERISTIC_UUID=8F605319-9B6B-EF59-93E3-E4A8B2FBBE89
```

### 권한 설정
#### Android (android/app/src/main/AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

#### iOS (ios/Runner/Info.plist)
```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>이 앱은 블루투스를 사용하여 다른 기기와 통신합니다.</string>
```

## 🚀 실행

```bash
# 의존성 설치
flutter pub get

# 앱 실행
flutter run
```

## 🔮 향후 계획

- [ ] 데이터베이스 연동 (SQLite/Hive)
- [ ] 클라우드 동기화
- [ ] 더 많은 신호 타입 지원
- [ ] 웹 대시보드
- [ ] AI 기반 패턴 학습
- [ ] 다중 디바이스 연결 지원

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
