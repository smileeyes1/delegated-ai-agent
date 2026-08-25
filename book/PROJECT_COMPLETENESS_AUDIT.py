#!/usr/bin/env python3
"""Non-generative completeness gate for the book factory.

It discovers missing work across the research-to-release lifecycle without
pretending that missing evidence exists. It only adds explicit, bounded tasks.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / 'FREE_QUEUE.json'
REPORT = ROOT / 'PROJECT_COMPLETENESS_REPORT.json'

queue = json.loads(QUEUE.read_text(encoding='utf-8'))
ids = {x.get('id') for x in queue}

gaps = [
    {
        'id': 'H001', 'title': 'السنة الصحيحة وتفصيل مسار التحول',
        'question': 'ما الذي تضيفه السنة الصحيحة إلى فهم أثر الوحي في الإنسان دون تجاوز ثبوت الحديث؟',
        'keywords': ['قال رسول الله', 'صحيح', 'هداية', 'إيمان']
    },
    {
        'id': 'T001', 'title': 'التفسير الموثوق وحدود الفهم',
        'question': 'ما الذي تضيفه مصادر التفسير الموثوقة إلى فهم الآيات المختارة، وما حدود الخلاف؟',
        'keywords': ['تفسير', 'قال ابن كثير', 'الطبري', 'القرطبي']
    },
    {
        'id': 'C001', 'title': 'خريطة الادعاءات والأدلة',
        'question': 'ما الادعاءات التي يمكن إثباتها من المادة المجموعة، وما درجة الدليل على كل ادعاء؟',
        'keywords': ['دليل', 'حجة', 'برهان', 'ادعاء']
    },
    {
        'id': 'X001', 'title': 'الأدلة المضادة والخلافات',
        'question': 'ما الأدلة أو القراءات التي قد تعارض الاستنتاجات الأولية، وكيف نقيّمها؟',
        'keywords': ['خلاف', 'استثناء', 'اعتراض', 'قراءة']
    },
    {
        'id': 'M001', 'title': 'من المعرفة إلى السلوك',
        'question': 'كيف ننتقل من النتيجة النصية الموثقة إلى تطبيق إنساني دون خلط النص بالتطبيق؟',
        'keywords': ['اعملوا', 'سلوك', 'عمل', 'مسؤولية']
    },
    {
        'id': 'B001', 'title': 'هندسة الكتاب والرحلة القارئية',
        'question': 'ما البنية التي تنقل القارئ من الفهم إلى الإيمان والعمل مع الحفاظ على حدود الدليل؟',
        'keywords': ['هداية', 'إيمان', 'عمل', 'تزكية']
    },
    {
        'id': 'QF001', 'title': 'تدقيق الاستشهادات والاقتباسات',
        'question': 'هل كل نص منسوب إلى القرآن أو السنة أو العلماء قابل للتتبع والتحقق؟',
        'keywords': ['توثيق', 'إسناد', 'مصدر', 'مرجع']
    },
    {
        'id': 'RF001', 'title': 'مراجعة نهائية مستقلة',
        'question': 'ما الأخطاء أو المبالغات أو الفجوات التي قد تبقى في المسودة قبل الإصدار؟',
        'keywords': ['مراجعة', 'خطأ', 'مبالغة', 'فجوة']
    },
]

added = []
for item in gaps:
    if item['id'] not in ids:
        item['status'] = 'pending'
        item['source'] = 'autonomous_completeness_audit'
        queue.append(item)
        added.append(item['id'])

report = {
    'status': 'GAPS_ADDED' if added else 'NO_NEW_GAPS',
    'queue_size': len(queue),
    'new_gap_ids': added,
    'required_dimensions': [
        'quran_corpus', 'hadith_authenticity', 'tafsir_context',
        'claim_evidence_matching', 'counter_evidence', 'uncertainty',
        'human_transformation', 'book_architecture', 'citation_audit',
        'independent_final_review', 'release_regression'
    ],
    'rule': 'gap discovery creates work; it never fabricates completion',
}
QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
