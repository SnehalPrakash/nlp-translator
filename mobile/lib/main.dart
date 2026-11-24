import 'package:flutter/material.dart';
import 'screens/translator_screen.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const IndicTranslatorApp());
}

class IndicTranslatorApp extends StatelessWidget {
  const IndicTranslatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IndicTranslate Offline',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      home: const TranslatorScreen(),
    );
  }
}
