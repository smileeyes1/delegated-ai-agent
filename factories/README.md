# درس دورة الماء

يولّد مصنع الوسائط مقطعًا تعليميًا متحركًا بالعربية مدته ١٢ ثانية. يصوّر التبخّر والتكاثف والهطول والتجمّع، ويولّد المؤثرات الصوتية محليًا. يمكن إضافة تسجيل صوتي عربي مأذون من ملف WAV محلي.

يتطلّب Python ٣٫١١ أو أحدث، وFFmpeg مع مرشّح `drawtext` الداعم لتشكيل العربية ومُرمّز `libx264`، و`ffprobe`، وخطًا يدعم العربية. المسار الافتراضي هو DejaVu Sans على Debian وUbuntu، ويمكن تحديد خط آخر باستخدام `--font`.

```sh
python -m factories.media --output-dir /tmp/hakim-water-cycle
python -m unittest discover -s tests -p 'test_media_factory.py'
```

يضم مجلد التسليم الفيديو `water-cycle.mp4`، والتسميات الزمنية القابلة لإعادة الاستخدام `captions.vtt`، وملف `manifest.json` الذي يسجّل نتيجة فحص الفيديو والصوت وبصمات SHA-256 للملفات. ينشر الأمر المجلد بعد نجاح التحقق ويحمي التسليم السابق عند إعادة استخدام مساره.

يُضاف تسجيل PCM WAV لا يتجاوز ١٢ ثانية بالخيار `--narration /path/to/local.wav`. تُضبط كتابة النص وتوقيته وفق المراحل الأربع في `media.py`.

المصدر العلمي لمراحل الدرس هو شرح هيئة المسح الجيولوجي الأمريكية لدورة الماء. [USGS Water Science School](https://www.usgs.gov/special-topics/water-science-school/science/water-cycle).
