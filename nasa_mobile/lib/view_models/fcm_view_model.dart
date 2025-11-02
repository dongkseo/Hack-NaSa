import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

class FcmViewModel with ChangeNotifier {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final AudioPlayer _audioPlayer = AudioPlayer();

  String? _fcmToken;
  String? get fcmToken => _fcmToken;

  // FCM 초기화 및 권한 요청
  Future<void> initialize() async {
    // 1. 권한 요청 (iOS & Android 13+)
    await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    // 2. FCM 토큰 가져오기
    _fcmToken = await _firebaseMessaging.getToken();
    debugPrint("FCM Token: $_fcmToken");

    // 3. 포그라운드 메시지 리스너 설정
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('Got a message whilst in the foreground!');
      debugPrint('Message data: ${message.data}');

      if (message.notification != null) {
        debugPrint('Message also contained a notification: ${message.notification}');
        // 포그라운드 상태에서 알림을 받으면 소리 재생
        playSound();
      }
    });
  }

  // 소리 재생 함수
  Future<void> playSound() async {
    try {
      // assets/sounds/alarm.mp3 파일을 재생합니다. 파일 경로는 실제 파일에 맞게 수정하세요.
      await _audioPlayer.play(AssetSource('sounds/sound1.wav'));
      debugPrint("Sound played successfully.");
    } catch (e) {
      debugPrint("Error playing sound: $e");
    }
  }
}
