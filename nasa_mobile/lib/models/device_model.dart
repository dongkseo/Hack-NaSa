import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';

class DeviceModel {
  final String id;
  final String name;
  final int rssi;
  final DeviceConnectionState connectionState;

  DeviceModel({
    required this.id,
    this.name = 'Unknown Device',
    this.rssi = 0,
    this.connectionState = DeviceConnectionState.disconnected,
  });

  factory DeviceModel.fromDiscoveredDevice(DiscoveredDevice device) {
    return DeviceModel(
      id: device.id,
      name: device.name.isNotEmpty ? device.name : 'Unknown Device',
      rssi: device.rssi,
      connectionState: DeviceConnectionState.disconnected,
    );
  }

  // GATT 통신을 위해 연결 상태를 변경하는 copyWith 메서드
  DeviceModel copyWith({
    String? id,
    String? name,
    int? rssi,
    DeviceConnectionState? connectionState,
  }) {
    return DeviceModel(
      id: id ?? this.id,
      name: name ?? this.name,
      rssi: rssi ?? this.rssi,
      connectionState: connectionState ?? this.connectionState,
    );
  }
}