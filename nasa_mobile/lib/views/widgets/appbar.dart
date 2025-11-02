import 'package:flutter/material.dart';

class HomeAppbar extends StatelessWidget implements PreferredSizeWidget {
  const HomeAppbar({super.key});

  @override
  Widget build(BuildContext context) {
    return AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          title: Image(
            image: AssetImage('assets/logo/nasa_logo.png'),
            height: 40,
          ),
        );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}