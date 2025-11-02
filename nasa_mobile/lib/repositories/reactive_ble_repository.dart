import 'dart:async';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'package:nasa_mobile/repositories/bluetooth_repository.dart';


class ReactiveBleRepository implements BluetoothRepository {
  final _ble = FlutterReactiveBle();

  // ⚠️ 실제 GATT 통신을 위한 UUID (백엔드 장치와 일치해야 함)
  static final Uuid serviceUuid = Uuid.parse('0000ABCD-0000-1000-8000-00805F9B34FB');
  static final Uuid characteristicUuid = Uuid.parse('0000EFGH-0000-1000-8000-00805F9B34FB');

  // 현재 연결된 장치의 ID (GATT 구독에 필요)
  String? _connectedDeviceId;

  @override
  Stream<BleStatus> get bleStatusStream => _ble.statusStream;

  @override
  Stream<DiscoveredDevice> scanForDevices(List<Uuid> serviceUuids) {
    // 60초 제한을 두고 스캔합니다.
    return _ble.scanForDevices(withServices: serviceUuids).timeout(const Duration(seconds: 60));
  }

  @override
  Stream<ConnectionStateUpdate> connectToDevice(String deviceId) {
    // GATT 구독을 위해 연결된 장치 ID 저장
    _connectedDeviceId = deviceId;
    
    // 장치 연결 및 연결 상태 업데이트 스트림 반환
    return _ble.connectToDevice(id: deviceId);
  }

  @override
  Stream<List<int>> subscribeToCharacteristic(QualifiedCharacteristic characteristic) {
    if (_connectedDeviceId == null || _connectedDeviceId != characteristic.deviceId) {
      // 연결되지 않았거나 ID가 일치하지 않으면 오류를 발생시킵니다.
      return Stream.error('Device not connected or ID mismatch for GATT subscription.');
    }
    
    // GATT Characteristic 구독 시작 (notify/indicate)
    return _ble.subscribeToCharacteristic(characteristic);
  }
}