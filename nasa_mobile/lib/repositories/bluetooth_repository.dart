import 'dart:async';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';

abstract class BluetoothRepository {
  
  // 블루투스 어댑터 상태 변화를 스트림으로 제공합니다.
  Stream<BleStatus> get bleStatusStream;

  // 특정 서비스 UUID를 가진 장치를 스캔합니다.
  Stream<DiscoveredDevice> scanForDevices(List<Uuid> serviceUuids);

  // 특정 장치에 연결하고 연결 상태 업데이트를 스트림으로 제공합니다.
  Stream<ConnectionStateUpdate> connectToDevice(String deviceId);

  // GATT Characteristic을 구독하여 데이터(notify)를 스트림으로 받습니다. (GATT 통신 핵심)
  Stream<List<int>> subscribeToCharacteristic(QualifiedCharacteristic characteristic);
}