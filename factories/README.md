# مصنع الدروس المتحركة

يولّد مصنع الوسائط دروسًا تعليمية متحركة بالعربية مع مؤثرات صوتية محلية. يعرض درس «دورة الماء» التبخّر والتكاثف والهطول والتجمّع في ١٢ ثانية. يتتبّع درس «كيف يتغيّر طول الظل؟» مسار الشمس وطول ظل جسم ثابت واتجاهه في ١٦ ثانية، ويختتم بسؤال للتجربة.

يتطلّب Python ٣٫١١ أو أحدث، وFFmpeg مع مرشّح `drawtext` الداعم لتشكيل العربية ومُرمّز `libx264`، و`ffprobe`، وخطًا يدعم العربية. المسار الافتراضي هو DejaVu Sans على Debian وUbuntu، ويمكن تحديد خط آخر باستخدام `--font`.

```sh
python -m factories.media --output-dir /tmp/hakim-water-cycle
python -m factories.media --lesson moving-shadows --output-dir /tmp/hakim-moving-shadows
python -m unittest discover -s tests -p 'test_media_factory.py'
```

يضم مجلد التسليم الفيديو باسم الدرس، والتسميات الزمنية القابلة لإعادة الاستخدام `captions.vtt`، وملف `manifest.json` الذي يسجّل نتيجة فحص الفيديو والصوت وبصمات SHA-256 للملفات. ينشر الأمر المجلد بعد نجاح التحقق ويحمي التسليم السابق عند إعادة استخدام مساره.

يُضاف تسجيل PCM WAV لا يتجاوز مدة الدرس بالخيار `--narration /path/to/local.wav`. تتبع الكتابة وتوقيت السرد مراحل الدرس الظاهرة في ملف التسميات.

المصدر العلمي لمراحل الدرس هو شرح هيئة المسح الجيولوجي الأمريكية لدورة الماء. [USGS Water Science School](https://www.usgs.gov/special-topics/water-science-school/science/water-cycle).

يحسب درس الظل طوله على أرض مستوية بقسمة ارتفاع الجسم على ظل زاوية ارتفاع الشمس. يحرّك الرسم زوايا افتراضية خلال اليوم لشرح العلاقة. [NOAA Solar Calculator](https://gml.noaa.gov/grad/solcalc/)
