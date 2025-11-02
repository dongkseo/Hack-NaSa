import 'package:flutter/material.dart';
import 'package:nasa_mobile/view_models/gesture_view_model.dart';
import 'package:provider/provider.dart';

class GestureMappingBottomSheet extends StatefulWidget {
  const GestureMappingBottomSheet({super.key});

  @override
  State<GestureMappingBottomSheet> createState() => _GestureMappingBottomSheetState();
}

class _GestureMappingBottomSheetState extends State<GestureMappingBottomSheet> {
  @override
  Widget build(BuildContext context) {
    final gestureViewmodel = context.watch<GestureViewModel>();
    final TextEditingController controller = TextEditingController();
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(top: 16, bottom: 32 + bottomInset, left: 16, right: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '새 제스처 매핑 추가',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).textTheme.bodyLarge!.color,
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            style: const TextStyle(color: Colors.white), // 텍스트 색상을 흰색으로 강제 지정
            decoration: InputDecoration(
              labelText: '제스처 입력',
              labelStyle: TextStyle(color: Colors.grey[400]), // 라벨 색상 지정
              enabledBorder: OutlineInputBorder(
                borderSide: BorderSide(color: Theme.of(context).colorScheme.secondary),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: BorderSide(color: Theme.of(context).colorScheme.secondary),
              ),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                // 제스처 매핑 저장 로직
                gestureViewmodel.addGestureMapping(
                  Icons.gesture,
                  controller.text,
                  '새 제스처 매핑',
                );
                Navigator.pop(context);

              },
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.auto_awesome),
                  const SizedBox(width: 8),
                  Text('저장'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}