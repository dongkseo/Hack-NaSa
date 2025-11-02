import 'package:flutter/material.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'package:nasa_mobile/view_models/ble_view_model.dart';
import 'package:nasa_mobile/view_models/fcm_view_model.dart';
import 'package:nasa_mobile/view_models/gesture_view_model.dart';
import 'package:nasa_mobile/views/widgets/appbar.dart';
import 'package:nasa_mobile/views/widgets/bottom_sheet.dart';
import 'package:nasa_mobile/views/widgets/card.dart';
import 'package:nasa_mobile/views/widgets/list_tile.dart';
import 'package:provider/provider.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    // 위젯이 빌드된 후 FcmViewModel 초기화
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FcmViewModel>().initialize();
    });
  }

  @override
  Widget build(BuildContext context) {
    final bleViewModel = context.watch<BleViewModel>();
    final gestureViewModel = context.watch<GestureViewModel>();

    return Scaffold(
      appBar: const HomeAppbar(),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. 상태 카드
            _buildStatusCard(context, bleViewModel),
            const SizedBox(height: 16),

            // 2. 기능 카드
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                ActionCard(
                  icon: Icons.alarm,
                  title: '알람',
                  onTap: () => bleViewModel.triggerSpeakerAction(),
                ),
                ActionCard(icon: Icons.music_note, title: '기능 2', onTap: null),
                ActionCard(
                  icon: Icons.notifications,
                  title: '기능 3',
                  onTap: null,
                ),
                ActionCard(icon: Icons.volume_up, title: '기능 4', onTap: null),
              ],
            ),
            const SizedBox(height: 24),

            // 3. 제스처 매핑
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('제스처 매핑', style: Theme.of(context).textTheme.titleLarge),
                IconButton(
                  onPressed: () {
                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      builder: (context) => const GestureMappingBottomSheet(),
                    );
                  },
                  icon: Icon(
                    Icons.add_circle,
                    color: Theme.of(context).colorScheme.secondary,
                    size: 32,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: ListView(
                children: gestureViewModel.gestureMappings
                    .map(
                      (gesture) => GestureListTile(
                        icon: gesture.icon,
                        title: gesture.title,
                        subtitle: gesture.subtitle,
                      ),
                    )
                    .toList(),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // 스캔 중이 아닐 때만 스캔 시작
          if (!bleViewModel.isScanning) {
            _showScanResults(context);
          }
        },
        child: bleViewModel.isScanning
            ? const CircularProgressIndicator(color: Colors.white)
            : const Icon(Icons.bluetooth_searching),
      ),
    );
  }

  // 상단 상태 카드 위젯
  Widget _buildStatusCard(BuildContext context, BleViewModel viewModel) {
    String title;
    String subtitle;
    Color statusColor;
    Widget trailing;

    if (viewModel.connectedDevice?.connectionState ==
        DeviceConnectionState.connected) {
      title = '연결됨: ${viewModel.connectedDevice!.name}';
      subtitle = viewModel.signalStatus;
      statusColor = Colors.green;
      trailing = const Icon(Icons.bluetooth_connected, color: Colors.green);
    } else if (viewModel.isScanning) {
      title = '기기 스캔 중...';
      subtitle = '주변의 BLE 기기를 찾고 있습니다.';
      statusColor = Colors.blue;
      trailing = const SizedBox(
        width: 24,
        height: 24,
        child: CircularProgressIndicator(),
      );
    } else {
      title = '연결 끊김';
      subtitle = '오른쪽 아래 버튼을 눌러 스캔을 시작하세요.';
      statusColor = Colors.grey;
      trailing = const Icon(Icons.bluetooth_disabled, color: Colors.grey);
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: statusColor, width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            trailing,
          ],
        ),
      ),
    );
  }

  // 스캔 결과 BottomSheet
  void _showScanResults(BuildContext context) {
    final bleViewModel = context.read<BleViewModel>();
    bleViewModel.startScan();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.5,
          maxChildSize: 0.9,
          minChildSize: 0.3,
          builder: (BuildContext context, ScrollController scrollController) {
            return ChangeNotifierProvider.value(
              value: bleViewModel,
              child: Consumer<BleViewModel>(
                builder: (context, viewModel, _) {
                  return Container(
                    color: Theme.of(context).scaffoldBackgroundColor,
                    child: Column(
                      children: [
                        Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Text(
                            '스캔된 기기',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                        ),
                        if (viewModel.scanResults.isEmpty &&
                            !viewModel.isScanning)
                          const Center(child: Text('스캔된 기기가 없습니다.'))
                        else if (viewModel.scanResults.isEmpty &&
                            viewModel.isScanning)
                          const Center(child: CircularProgressIndicator())
                        else
                          Expanded(
                            child: ListView.builder(
                              controller: scrollController,
                              itemCount: viewModel.scanResults.length,
                              itemBuilder: (context, index) {
                                final device = viewModel.scanResults[index];
                                return Card(
                                  margin: const EdgeInsets.symmetric(
                                    horizontal: 16,
                                    vertical: 4,
                                  ),
                                  child: ListTile(
                                    title: Text(device.name),
                                    subtitle: Text(
                                      'ID: ${device.id}\nRSSI: ${device.rssi}',
                                    ),
                                    trailing: ElevatedButton(
                                      onPressed: () {
                                        viewModel.connectToDevice(device);
                                        Navigator.pop(
                                          context,
                                        ); // Close bottom sheet
                                      },
                                      child: const Text('연결'),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                      ],
                    ),
                  );
                },
              ),
            );
          },
        );
      },
    ).whenComplete(() {
      bleViewModel.stopScan();
    });
  }
}
