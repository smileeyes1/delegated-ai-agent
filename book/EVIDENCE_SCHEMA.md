# Evidence Ledger Schema

كل دعوى مهمة تسجل بهذا الترتيب:

1. `claim_id`
2. `claim` — الدعوى بصياغة قابلة للاختبار.
3. `source_type` — قرآن / سنة صحيحة / تفسير / لغة / تاريخ.
4. `source_reference` — السورة والآية أو الحديث والتخريج أو المرجع.
5. `source_text_or_pointer` — النص أو موضعه دون اقتباس زائد.
6. `authenticity` — ثابت / صحيح / حسن / مختلف فيه / غير صالح.
7. `direct_meaning` — ما يدل عليه النص مباشرة.
8. `interpretation` — فهم العلماء أو التفسير، مع نسبته.
9. `inference` — الاستنتاج الذي يبنيه الكتاب.
10. `application` — إن وُجد، مع فصله عن الدليل.
11. `counter_evidence` — الأدلة المخالفة أو المقيدة.
12. `confidence` — مرتفع / متوسط / منخفض.
13. `status` — candidate / verified / disputed / rejected.

## قاعدة
لا يجوز تحويل `interpretation` أو `inference` إلى `source_text`، ولا تحويل دعوى ضعيفة إلى حقيقة بسبب تكرارها في مصادر ثانوية.
