import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../models/translation.dart';
import '../services/api_service.dart';

class TranslatorScreen extends StatefulWidget {
  const TranslatorScreen({super.key});

  @override
  State<TranslatorScreen> createState() => _TranslatorScreenState();
}

class _TranslatorScreenState extends State<TranslatorScreen> {
  final ApiService _apiService = ApiService();
  final FlutterTts _flutterTts = FlutterTts();
  final TextEditingController _inputController = TextEditingController();

  List<Language> _languages = [];
  String _sourceLang = "auto";
  String _targetLang = "kn";

  bool _isLoading = false;
  TranslationResponse? _lastResult;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _initEngine();
    _inputController.addListener(_onTextChanged);
  }

  Future<void> _initEngine() async {
    await _apiService.init();
    final langs = await _apiService.getLanguages();
    if (mounted) {
      setState(() {
        _languages = langs;
      });
    }
  }

  void _onTextChanged() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 600), () {
      if (_inputController.text.trim().isNotEmpty) {
        _performTranslation();
      } else {
        setState(() {
          _lastResult = null;
        });
      }
    });
  }

  Future<void> _performTranslation() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isLoading = true);
    final res = await _apiService.translate(
      text: text,
      sourceLang: _sourceLang,
      targetLang: _targetLang,
    );

    if (mounted) {
      setState(() {
        _isLoading = false;
        _lastResult = res;
      });
    }
  }

  void _swapLanguages() {
    if (_sourceLang == "auto") {
      setState(() {
        _sourceLang = "en";
        final temp = _sourceLang;
        _sourceLang = _targetLang;
        _targetLang = temp;
      });
    } else {
      setState(() {
        final temp = _sourceLang;
        _sourceLang = _targetLang;
        _targetLang = temp;
      });
    }
    if (_lastResult != null && _lastResult!.translatedText.isNotEmpty) {
      _inputController.text = _lastResult!.translatedText;
    } else {
      _performTranslation();
    }
  }

  Future<void> _speakText(String text, String langCode) async {
    await _flutterTts.setLanguage(langCode);
    await _flutterTts.speak(text);
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: _apiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Server Settings"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Default is http://translator.local:8000. If your Wi-Fi router blocks mDNS, enter your Mac's IP (e.g. http://192.168.1.15:8000).",
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: "Server URL",
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              await _apiService.setCustomHost(controller.text);
              Navigator.pop(ctx);
              setState(() {});
            },
            child: const Text("Save & Connect"),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _inputController.dispose();
    _flutterTts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isConnected = _apiService.isConnected;

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text("🌐 IndicTranslate"),
            SizedBox(width: 8),
            Text(
              "Offline",
              style: TextStyle(
                fontSize: 12,
                color: Color(0xFF10B981),
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          GestureDetector(
            onTap: _showSettingsDialog,
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: isConnected
                    ? Colors.green.withOpacity(0.15)
                    : Colors.amber.withOpacity(0.15),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isConnected ? Colors.green : Colors.amber,
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.circle,
                    size: 8,
                    color: isConnected ? Colors.green : Colors.amber,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    isConnected ? "Connected" : "Setup Host",
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: isConnected
                          ? Colors.green.shade800
                          : Colors.amber.shade900,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Warning Banner for Romanized Indic Text
            if (_lastResult?.warning != null)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF3C7),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFFDE68A)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: Color(0xFF92400E)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _lastResult!.warning!,
                        style: const TextStyle(
                          color: Color(0xFF92400E),
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

            // Language Selector Bar
            Card(
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    DropdownButton<String>(
                      value: _sourceLang,
                      underline: const SizedBox(),
                      items: [
                        const DropdownMenuItem(
                          value: "auto",
                          child: Text("🌐 Auto-Detect"),
                        ),
                        ..._languages.map(
                          (l) => DropdownMenuItem(
                            value: l.code,
                            child: Text(l.name),
                          ),
                        ),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setState(() => _sourceLang = val);
                          _performTranslation();
                        }
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.swap_horiz),
                      onPressed: _swapLanguages,
                    ),
                    DropdownButton<String>(
                      value: _targetLang,
                      underline: const SizedBox(),
                      items: _languages
                          .map(
                            (l) => DropdownMenuItem(
                              value: l.code,
                              child: Text(l.name),
                            ),
                          )
                          .toList(),
                      onChanged: (val) {
                        if (val != null) {
                          setState(() => _targetLang = val);
                          _performTranslation();
                        }
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Input Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    TextField(
                      controller: _inputController,
                      maxLines: 4,
                      style: const TextStyle(fontSize: 18),
                      decoration: const InputDecoration(
                        hintText: "Type text to translate...",
                        border: InputBorder.none,
                      ),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "${_inputController.text.length} chars",
                          style:
                              TextStyle(color: Colors.grey.shade600, fontSize: 12),
                        ),
                        if (_inputController.text.isNotEmpty)
                          IconButton(
                            icon: const Icon(Icons.close, size: 20),
                            onPressed: () {
                              _inputController.clear();
                              setState(() => _lastResult = null);
                            },
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Output Translation Card
            Card(
              color: Theme.of(context).brightness == Brightness.dark
                  ? const Color(0xFF1E293B)
                  : const Color(0xFFEFF6FF),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_isLoading)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: CircularProgressIndicator(),
                        ),
                      )
                    else ...[
                      SelectableText(
                        _lastResult?.translatedText ??
                            "Translation will appear here...",
                        style: TextStyle(
                          fontSize: 18,
                          color: _lastResult == null
                              ? Colors.grey.shade500
                              : null,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          if (_lastResult != null)
                            Text(
                              "⏱️ ${_lastResult!.latencyMs}ms (${_lastResult!.cached ? 'Cached' : 'INT8 CPU'})",
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            )
                          else
                            const SizedBox(),
                          Row(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.volume_up, size: 20),
                                onPressed: _lastResult != null
                                    ? () => _speakText(
                                          _lastResult!.translatedText,
                                          _targetLang,
                                        )
                                    : null,
                              ),
                              IconButton(
                                icon: const Icon(Icons.copy, size: 20),
                                onPressed: _lastResult != null
                                    ? () {
                                        Clipboard.setData(ClipboardData(
                                          text: _lastResult!.translatedText,
                                        ));
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                            content: Text("Copied to clipboard"),
                                            duration: Duration(seconds: 1),
                                          ),
                                        );
                                      }
                                    : null,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // Offline Dictionary Card
            if (_lastResult?.dictionaryEntry != null) ...[
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.menu_book, color: Color(0xFF2563EB)),
                          const SizedBox(width: 8),
                          Text(
                            _lastResult!.dictionaryEntry!.word.toUpperCase(),
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF2563EB),
                            ),
                          ),
                          if (_lastResult!.dictionaryEntry!.pos != null) ...[
                            const SizedBox(width: 8),
                            Text(
                              "(${_lastResult!.dictionaryEntry!.pos})",
                              style: TextStyle(
                                fontStyle: FontStyle.italic,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _lastResult!.dictionaryEntry!.definition ?? "",
                        style: const TextStyle(fontSize: 14),
                      ),
                      if (_lastResult!.dictionaryEntry!.synonyms.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          children: [
                            const Text("Synonyms: ",
                                style: TextStyle(fontWeight: FontWeight.w600)),
                            ..._lastResult!.dictionaryEntry!.synonyms.map(
                              (s) => Chip(
                                label: Text(s, style: const TextStyle(fontSize: 11)),
                                visualDensity: VisualDensity.compact,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
