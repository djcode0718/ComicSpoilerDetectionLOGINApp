import 'package:flutter/material.dart';
import 'package:comic_spoiler_login_frontend/screens/login_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    print(LoginPage);
    return MaterialApp(
      title: 'Comic Spoiler Login App',
      debugShowCheckedModeBanner: false,
      home: LoginPage(), // ✅ here!
    );
  }
}
