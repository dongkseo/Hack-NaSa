import 'package:flutter/material.dart';
import 'package:nasa_mobile/models/gesture_model.dart';

class GestureViewModel extends ChangeNotifier {
  // 제스처 매핑 데이터
  final List<GestureModel> _gestureMappings = [
    GestureModel(icon: Icons.gesture, title: '손 흔들기', subtitle: '알람 작동'),
    GestureModel(icon: Icons.gesture, title: '주먹 쥐기', subtitle: '기능 2 작동'),
    GestureModel(icon: Icons.gesture, title: '손바닥 펴기', subtitle: '기능 3 작동'),
  ];

  List<GestureModel> get gestureMappings => _gestureMappings;

  // 제스처 추가
  void addGestureMapping(IconData icon, String title, String subtitle) {
    _gestureMappings.add(GestureModel(icon: icon, title: title, subtitle: subtitle));
    notifyListeners();
  }

  // 제스처 제거
  void removeGestureMapping(GestureModel gesture) {
    _gestureMappings.remove(gesture);
    notifyListeners();
  }
}