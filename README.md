# delegated-ai-agent
Delegated AI Agent – Human-authorized AI assistant (GitHub-first)

## تشغيل حكيم محليًا

يتحقق المحرك من ملفات JSON ويحسب بصمات SHA-256 ببايثون وSQLite من دون نموذج أو اتصال خارجي. ثبّت معرّفًا لكل مهمة، ثم استعمل قاعدة البيانات نفسها عند الاستئناف.

```bash
python3 -m app.main enqueue book-state verify-json book/CHAPTER_01_STATE.json
python3 -m app.main run-next
python3 -m app.main history book-state
python3 -m app.main backup /tmp/hakim-queue-backup.sqlite3
```

تعمل `run-next` لمحاولة واحدة، ويعالج `drain --limit 20` دفعة محدودة. تعرض `status` المهام ونتائجها، وتعيد `retry <id>` مهمة فاشلة إلى الطابور لمحاولة إضافية. افحص نسخة رجوع باستخدام الخيار العام `--db` ومسار مساحة العمل الأصلية. خزّن قواعد التشغيل المحلية والنسخ الخاصة خارج Git.

تتطلب قراءة المدخلات نظام POSIX يدعم فتح الملفات انطلاقًا من واصف المجلد. ضع النسخ الاحتياطية في مجلد موثوق على نظام ملفات يدعم الروابط الصلبة.

- [مصنع الوسائط ودرس دورة الماء](factories/README.md)
- [عقد تبادل نقاط الاستئناف](interop/README.md)
- [تعليمات هندسة حكيم](AGENTS.md)
