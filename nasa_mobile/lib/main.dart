import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:nasa_mobile/core/themas/thema.dart';
import 'package:nasa_mobile/firebase_options.dart';
import 'package:nasa_mobile/repositories/reactive_ble_repository.dart';
import 'package:nasa_mobile/view_models/ble_view_model.dart';
import 'package:nasa_mobile/view_models/fcm_view_model.dart';
import 'package:nasa_mobile/view_models/gesture_view_model.dart';
import 'package:nasa_mobile/views/home.dart';
import 'package:provider/provider.dart';
import 'package:audioplayers/audioplayers.dart';

// 백그라운드 메시지 처리를 위한 최상위 함수
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // 백그라운드에서 메시지를 처리하기 전에 Firebase를 초기화해야 합니다.
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  debugPrint("Handling a background message: ${message.messageId}");

  // 백그라운드에서 소리 재생
  final AudioPlayer audioPlayer = AudioPlayer();
  await audioPlayer.play(AssetSource('sounds/sound1.wav'));
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: "assets/.env");

  // Firebase 초기화
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // 백그라운드 메시지 핸들러 설정
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  runApp(
    MultiProvider(
      providers: [
        Provider<ReactiveBleRepository>(
          create: (_) => ReactiveBleRepository(),
        ),
        ChangeNotifierProvider(
          create: (context) => BleViewModel(
            context.read<ReactiveBleRepository>(),
          ),
        ),
        ChangeNotifierProvider(
          create: (_) => GestureViewModel(),
        ),
        ChangeNotifierProvider(
          create: (_) => FcmViewModel(),
        ),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NaSa Mobile',
      theme: AppTheme.darkTheme,
      home: const HomePage(),
    );
  }
}