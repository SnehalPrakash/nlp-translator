import 'package:flutter_test/flutter_test.dart';
import 'package:indic_translator_mobile/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const IndicTranslatorApp());
    expect(find.text('🌐 IndicTranslate'), findsOneWidget);
  });
}
