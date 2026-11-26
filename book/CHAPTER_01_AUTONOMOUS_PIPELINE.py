"""Evidence-controlled autonomous pipeline for Chapter 01.

Acquires primary Quran text from Tanzil, checks the same verses in the
Quranpedia Hafs Uthmani encoding, and preserves both source texts. Only a
complete text match can replace the evidence map and bounded research draft.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen

if __package__:
    from .chapter_sources import COMPARISON_METHOD, quranpedia_text, verify_verse
else:
    from chapter_sources import COMPARISON_METHOD, quranpedia_text, verify_verse

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'research_data'
BASE='https://api.quranpedia.net/v1'
TANZIL_URL = ('https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2'
              '&agree=true&marks=true&sajdah=true&rub=true&stanween=true')
UA='BOOK_FACTORY/1.1 (evidence research runner)'
REFS=['2:2','2:185','5:15','5:16','10:57','14:1','16:89','17:9','29:45','39:23','57:16','62:2','91:9']
POS={'هدى':'guidance','تزكية':'purification','ذكر':'remembrance','تقوى':'taqwa','رحمة':'mercy','إصلاح':'reform','عدل':'justice','إحسان':'excellence','عباد':'worship/service','صلو':'prayer'}
COUNTER={'ضلال':'misguidance','ظلم':'wrongdoing','قسو':'hardness','غفل':'heedlessness','نفاق':'hypocrisy','إعراض':'turning-away','كذب':'denial/lying'}

def get(url):
    with urlopen(Request(url, headers={'User-Agent': UA}), timeout=30) as response:
        return response.read()

def norm(s):
    s=s or ''
    s=s.replace('\ufeff','')
    s=re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]','',s)
    s=s.translate(str.maketrans({'ٱ':'ا','أ':'ا','إ':'ا','آ':'ا','ى':'ي','ة':'ة'}))
    return re.sub(r'\s+','',s)

def load_tanzil():
    raw = get(TANZIL_URL)
    verses = {}
    for line in raw.decode('utf-8-sig').splitlines():
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([0-9]+)\|([0-9]+)\|([^|]+)', line)
        if match is None:
            raise ValueError('Unexpected Tanzil export row')
        surah, ayah, text = match.groups()
        ref = f'{surah}:{ayah}'
        if ref in verses or not text.strip():
            raise ValueError(f'Duplicate or empty Tanzil verse {ref}')
        verses[ref] = text
    missing = set(REFS + ['1:1']).difference(verses)
    if len(verses) != 6236 or missing:
        raise ValueError(f'Incomplete Tanzil export. Missing chapter references: {sorted(missing)}')
    return verses, raw

def qpedia(ref):
    url = f'{BASE}/mushafs/1/{ref.replace(":", "/")}'
    raw = get(url)
    return quranpedia_text(ref, json.loads(raw)), {'url': url, 'sha256': hashlib.sha256(raw).hexdigest()}

def tafsir(ref,book=1):
    return json.loads(get(f'{BASE}/ayah/{ref.replace(":", "/")}/book/{book}'))

def nearby(ref,verses,window=2):
    s,a=map(int,ref.split(':')); return {f'{s}:{n}':verses[f'{s}:{n}'] for n in range(max(1,a-window),a+window+1) if f'{s}:{n}' in verses}

def hits(probes,all_text):
    out=[]
    for term,label in probes.items():
        for line in all_text.splitlines():
            ref,txt=line.split('|',1)
            if term in norm(txt): out.append({'reference':ref,'matched_probe':term,'category':label})
    seen=set(); unique=[]
    for x in out:
        k=(x['reference'],x['matched_probe'])
        if k not in seen: seen.add(k); unique.append(x)
    return unique

def collect_texts(verses):
    records = []
    for ref in REFS:
        quranpedia, provenance = qpedia(ref)
        primary = verses[ref]
        matches = verify_verse(ref, primary, quranpedia, verses['1:1'])
        records.append({
            'id': 'Q01-' + ref.replace(':', '-'),
            'reference': ref,
            'primary_text': primary,
            'quranpedia_text': quranpedia,
            'quranpedia_source': provenance,
            'text_crosscheck': 'MATCH' if matches else 'MISMATCH',
            'crosscheck_method': COMPARISON_METHOD,
            'context': nearby(ref, verses),
            'status': 'verified_text' if matches else 'BLOCKED_TEXT_MISMATCH',
        })
    return records


def add_tafsir(records):
    for record in records:
        try:
            commentary = tafsir(record['reference'])
            if not isinstance(commentary, dict):
                raise ValueError('Unexpected Quranpedia tafsir response')
            record['tafsir_book'] = commentary.get('book', {})
            record['tafsir_content'] = commentary.get('content', [])
        except (ValueError, OSError) as exc:
            record['tafsir_book'] = {}
            record['tafsir_content'] = []
            record['tafsir_error'] = str(exc)


def build_draft(records, counter_count):
    question = "What does the Qur'an itself say revelation is intended to produce in the human being?"
    clusters = {
        'guidance': ['2:2', '2:185', '5:15', '5:16', '10:57', '14:1', '16:89', '17:9'],
        'heart/soul transformation': ['10:57', '39:23', '57:16', '91:9'],
        'embodied ethical effect': ['29:45', '62:2'],
    }
    cluster_records = {
        cluster: [r for r in records if r['reference'] in refs]
        for cluster, refs in clusters.items()
    }
    argument_map = {
        'question': question,
        'observed_clusters': [
            {'cluster': cluster, 'evidence_ids': [r['id'] for r in support]}
            for cluster, support in cluster_records.items()
        ],
        'counter_evidence_probe_count': counter_count,
        'status': 'research_synthesis_not_final_verdict',
    }
    lines = [
        '# الفصل ٠١ — مسودة بحثية مضبوطة', '',
        '> الحالة: مسودة بحثية آلية. لا تمثل حكمًا نهائيًا، ولا تدّعي استنفاد القرآن في سؤالها.', '',
        '## السؤال', question, '', '## ما تثبته المادة النصية في هذه الجولة',
    ]
    for cluster, support in cluster_records.items():
        if support:
            refs = ', '.join(r['reference'] for r in support)
            lines.append(f'- يظهر محور **{cluster}** في هذه العينة من المواضع: {refs}. '
                         'تحتاج دلالة الآيات مجتمعة على سؤال الفصل إلى مراجعة تفسيرية.')
    lines += [
        '', '## شرط عدم التسرع',
        f'- طابق التحقق النص في {len(records)} موضعًا بين تنزيل وقرآن بيديا بعد توحيد علامات الرسم المحددة.',
        f'- رصد البحث المضاد {counter_count} مطابقةً لمؤشرات لغوية مضادة.',
        '- تحتاج هذه المواضع إلى قراءة في سياقها قبل الاستدلال بها.',
        '', '## ما لم يُحسم',
        '- العلاقة بين هذه الآيات وبين غاية الوحي تحتاج مقارنة تفسيرية أوسع ودراسة السياقات '
        'وتحديد درجة الاتفاق والخلاف بين المفسرين.',
        '- يحتاج الاستدلال من تكرار محور لغوي إلى استقراء أوسع ومراجعة نقدية.',
        '', '## قرار البوابة',
        'الانتقال إلى الكتابة النهائية محجوب حتى يكتمل الاستقراء المقارن للأدلة والتفسيرات '
        'ويُختبر ضد الاعتراضات.',
    ]
    return argument_map, '\n'.join(lines)


def publish(data_dir, raw_tanzil, artifact):
    data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=data_dir) as temporary:
        staging = Path(temporary)
        files = {
            'tanzil-uthmani.txt': raw_tanzil,
            'chapter_01_research_draft.md': (artifact['draft'] + '\n').encode('utf-8'),
            'chapter_01_autonomous_research.json': (
                json.dumps(artifact, ensure_ascii=False, indent=2) + '\n'
            ).encode('utf-8'),
        }
        for name, data in files.items():
            (staging / name).write_bytes(data)
        # Readers use the evidence JSON as the authoritative checkpoint.
        for name in files:
            (staging / name).replace(data_dir / name)


def run(data_dir):
    try:
        verses, raw_tanzil = load_tanzil()
        records = collect_texts(verses)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': 'SOURCE_ACQUISITION', 'detail': str(exc)},
                         ensure_ascii=False))
        return 2

    mismatches = [r['reference'] for r in records if r['text_crosscheck'] != 'MATCH']
    if mismatches:
        print(json.dumps({
            'status': 'BLOCKED',
            'reason': 'TEXT_MISMATCH',
            'verified_text_count': len(records) - len(mismatches),
            'mismatches': mismatches,
        }, ensure_ascii=False))
        return 2

    add_tafsir(records)
    all_text = '\n'.join(f'{ref}|{text}' for ref, text in verses.items())
    counter, positive = hits(COUNTER, all_text), hits(POS, all_text)
    argument_map, draft = build_draft(records, len(counter))
    artifact = {
        'run_at': datetime.now(timezone.utc).isoformat(),
        'source': {
            'name': 'Tanzil Project',
            'url': TANZIL_URL,
            'sha256': hashlib.sha256(raw_tanzil).hexdigest(),
            'license': 'CC BY 3.0, verbatim text with attribution',
        },
        'cross_source': 'Quranpedia Hafs Uthmani API',
        'crosscheck_basmalah': verses['1:1'],
        'refs': REFS,
        'verified_text_count': len(records),
        'records': records,
        'positive_lexical_scan': positive[:500],
        'counter_evidence_scan': counter[:500],
        'argument_map': argument_map,
        'draft_status': 'BOUNDED_RESEARCH_DRAFT',
        'draft': draft,
    }
    publish(data_dir, raw_tanzil, artifact)
    print(json.dumps({'status': 'PASS', 'verified_text_count': len(records), 'counter_scan': len(counter)},
                     ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=DATA)
    raise SystemExit(run(parser.parse_args().output_dir))


if __name__ == '__main__':
    main()
