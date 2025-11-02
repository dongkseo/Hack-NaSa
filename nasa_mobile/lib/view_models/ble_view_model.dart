import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'package:nasa_mobile/models/device_model.dart';
import 'package:nasa_mobile/repositories/bluetooth_repository.dart';
import 'package:nasa_mobile/repositories/reactive_ble_repository.dart';
import 'package:audioplayers/audioplayers.dart';


class BleViewModel with ChangeNotifier {
  final BluetoothRepository _repository;
  final AudioPlayer _audioPlayer = AudioPlayer();
  
  // 상태 관리 변수
  List<DeviceModel> _scanResults = [];
  bool _isScanning = false;
  String _signalStatus = '미연결';
  DeviceModel? _connectedDevice;

  // Getter
  List<DeviceModel> get scanResults => _scanResults;
  bool get isScanning => _isScanning;
  String get signalStatus => _signalStatus;
  DeviceModel? get connectedDevice => _connectedDevice;

  // Stream Subscription
  StreamSubscription? _scanSubscription;
  StreamSubscription? _connectionSubscription;
  StreamSubscription? _gattSubscription;

  BleViewModel(this._repository);

  // --- 1. 스캔 로직 ---
  void startScan() {
    _scanResults.clear();
    _isScanning = true;
    notifyListeners();

    // 백엔드 장치의 Service UUID를 기준으로 스캔
    final serviceUuids = [ReactiveBleRepository.serviceUuid];

    _scanSubscription?.cancel();
    _scanSubscription = _repository
        .scanForDevices(serviceUuids)
        .listen((device) {
          final newDevice = DeviceModel.fromDiscoveredDevice(device);
          // 중복 방지 및 업데이트 로직
          if (!_scanResults.any((d) => d.id == newDevice.id)) {
            _scanResults.add(newDevice);
            notifyListeners();
          }
        }, onError: (e) {
          _isScanning = false;
          print('Scan Error: $e');
          notifyListeners();
        });

    // 4초 후 자동 중지 (옵션)
    Future.delayed(const Duration(seconds: 4), stopScan);
  }

  void stopScan() {
    _scanSubscription?.cancel();
    _isScanning = false;
    notifyListeners();
  }

  // --- 2. 연결 및 GATT 구독 로직 ---
  void connectToDevice(DeviceModel device) {
    _signalStatus = '연결 중...';
    notifyListeners();

    _connectionSubscription?.cancel();
    _connectionSubscription = _repository
        .connectToDevice(device.id)
        .listen((update) {
          final newState = update.connectionState;
          _connectedDevice = device.copyWith(connectionState: newState);

          if (newState == DeviceConnectionState.connected) {
            _signalStatus = '연결됨. GATT 리스닝 시작...';
            _startGattListener(device.id); // 👈 연결 성공 시 GATT 구독 시작
          } else if (newState == DeviceConnectionState.disconnected) {
            _signalStatus = '연결 해제됨';
            _gattSubscription?.cancel();
            _connectedDevice = null;
          }
          notifyListeners();
        });
  }

  // --- 3. GATT 구독 및 기능 실행 로직 ---
  void _startGattListener(String deviceId) {
    final characteristic = QualifiedCharacteristic(
        serviceId: ReactiveBleRepository.serviceUuid,
        characteristicId: ReactiveBleRepository.characteristicUuid,
        deviceId: deviceId,
    );

    _gattSubscription?.cancel();
    _gattSubscription = _repository
        .subscribeToCharacteristic(characteristic)
        .listen((dataBytes) {
          final signal = String.fromCharCodes(dataBytes).trim();
          _handleReceivedSignal(signal); // 신호에 따라 기능 실행
        });
  }

  void _handleReceivedSignal(String signal) {
    _signalStatus = '신호 수신: $signal';
    
    // GATT 신호에 따른 원하는 기능 실행
    if (signal == 'LOCK_TRIGGER') {
      triggerSpeakerAction();
    }
    
    notifyListeners();
  }

  // 4. 원하는 기능: 오디오 재생
  void triggerSpeakerAction() async {
    print('🚨 스피커 액션 트리거! 오디오 재생.');
    await _audioPlayer.play(AssetSource('sounds/sound1.wav'));
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    _connectionSubscription?.cancel();
    _gattSubscription?.cancel();
    _audioPlayer.dispose();
    super.dispose();
  }
}