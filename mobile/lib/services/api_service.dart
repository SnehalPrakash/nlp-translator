import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/translation.dart';

class ApiService {
  static const String _defaultHost = "http://translator.local:8000";
  static const String _prefKeyHost = "custom_server_host";

  String _baseUrl = _defaultHost;
  bool _isConnected = false;

  String get baseUrl => _baseUrl;
  bool get isConnected => _isConnected;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_prefKeyHost) ?? _defaultHost;
    await checkConnection();
  }

  Future<void> setCustomHost(String host) async {
    var formatted = host.trim();
    if (!formatted.startsWith("http://") && !formatted.startsWith("https://")) {
      formatted = "http://$formatted";
    }
    if (!formatted.contains(":", 5)) {
      formatted = "$formatted:8000";
    }
    _baseUrl = formatted;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKeyHost, _baseUrl);
    await checkConnection();
  }

  Future<bool> checkConnection() async {
    try {
      final response = await http
          .get(Uri.parse("$_baseUrl/api/languages"))
          .timeout(const Duration(seconds: 3));
      _isConnected = response.statusCode == 200;
    } catch (_) {
      _isConnected = false;
    }
    return _isConnected;
  }

  Future<List<Language>> getLanguages() async {
    try {
      final res = await http.get(Uri.parse("$_baseUrl/api/languages"));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        final list = data['languages'] as List;
        return list.map((e) => Language.fromJson(e)).toList();
      }
    } catch (e) {
      // Fallback offline list
    }
    return const [
      Language(code: "kn", name: "Kannada (ಕನ್ನಡ)"),
      Language(code: "hi", name: "Hindi (हिन्दी)"),
      Language(code: "ta", name: "Tamil (தமிழ்)"),
      Language(code: "te", name: "Telugu (తెలుగు)"),
      Language(code: "ml", name: "Malayalam (മലയാളം)"),
      Language(code: "en", name: "English"),
      Language(code: "es", name: "Spanish (Español)"),
      Language(code: "fr", name: "French (Français)"),
    ];
  }

  Future<TranslationResponse?> translate({
    required String text,
    required String sourceLang,
    required String targetLang,
  }) async {
    try {
      final response = await http.post(
        Uri.parse("$_baseUrl/api/translate"),
        headers: {"Content-Type": "application/json"},
        body: json.encode({
          "text": text,
          "source_lang": sourceLang,
          "target_lang": targetLang,
          "use_cache": true,
          "save_history": true,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return TranslationResponse.fromJson(data);
      }
    } catch (e) {
      // Connection issue
    }
    return null;
  }
}
