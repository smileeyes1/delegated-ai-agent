"""Evidence-controlled autonomous pipeline for Chapter 01.

Runs without a paid model. It acquires primary text from Tanzil, cross-checks
ayahs against Quranpedia's Hafs API, retrieves a classical tafsir record,
collects lexical counter-evidence from the complete Tanzil text, and emits an
auditable evidence map, argument map, and bounded research draft.

Important: generated synthesis is explicitly a research draft, not an
unqualified religious verdict. No claim is promoted beyond its evidence.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
import hashlib, json, re
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'research_data'; DATA.mkdir(exist_ok=True)
BASE='https://api.quranpedia.net/v1'
UA='BOOK_FACTORY/1.0 (evidence research runner)'
REFS=['2:2','2:185','5:15','5:16','10:57','14:1','16:89','17:9','29:45','39:23','57:16','62:2','91:9']
# Terms are search probes, not conclusions.
POS={'هدى':'guidance','تزكية':'purification','ذكر':'remembrance','تقوى':'taqwa','رحمة':'mercy','إصلاح':'reform','عدل':'justice','إحسان':'excellence','عباد':'worship/service','صلو':'prayer'}
COUNTER={'ضلال':'misguidance','ظلم':'wrongdoing','قسو':'hardness','غفل':'heedlessness','نفاق':'hypocrisy','إعراض':'turning-away','كذب':'denial/lying'}

def get(url):
    r=urlopen(Request(url,headers={'User-Agent':UA}),timeout=30)
    b=r.read(); return b, r.headers.get('content-type','')

def norm(s):
    return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]','',s or '')

def load_tanzil():
    url='https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true&marks=true&sajdah=true&rub=true&stanween=true'
    b,_=get(url); text=b.decode('utf-8-sig')
    (DATA/'tanzil-uthmani.txt').write_text(text,encoding='utf-8')
    sha=hashlib.sha256(b).hexdigest(); verses={}
    for line in text.splitlines():
        p=line.split('|',2)
        if len(p)==3: verses[f'{p[0]}:{p[1]}']=p[2].strip()
    return verses,sha,url

def qpedia(ref):
    s,a=map(int,ref.split(':'))
    b,_=get(f'{BASE}/mushafs/1/{s}/{a}')
    return json.loads(b)

def tafsir(ref,book=1):
    s,a=map(int,ref.split(':'))
    b,_=get(f'{BASE}/ayah/{s}/{a}/book/{book}')
    return json.loads(b)

def nearby(ref,verses,window=2):
    s,a=map(int,ref.split(':')); out={}
    for n in range(max(1,a-window),a+window+1):
        k=f'{s}:{n}'
        if k in verses: out[k]=verses[k]
    return out

verses,sha,tanzil_url=load_tanzil()
missing=[r for r in REFS if r not in verses]
if missing: raise SystemExit(f'Missing primary text: {missing}')

records=[]
for ref in REFS:
    q=qpedia(ref); qp=norm(q.get('text',''))
    tz=norm(verses[ref])
    same=qp==tz
    try: tf=tafsir(ref,1)
    except Exception as e: tf={'error':str(e)}
    records.append({'id':'Q01-'+ref.replace(':','-'),'reference':ref,'primary_text':verses[ref],
                    'quranpedia_text':q.get('text'), 'text_crosscheck':'MATCH' if same else 'MISMATCH',
                    'context':nearby(ref,verses), 'tafsir_book':tf.get('book',{}),
                    'tafsir_content':tf.get('content',[]), 'status':'verified_text' if same else 'BLOCKED_TEXT_MISMATCH'})

all_text='\n'.join(f'{k}|{v}' for k,v in verses.items())
def hits(probes):
    out=[]
    for term,label in probes.items():
        for line in all_text.splitlines():
            ref,txt=line.split('|',1)
            if term in norm(txt): out.append({'reference':ref,'matched_probe':term,'category':label})
    return out
counter=hits(COUNTER)
positive=hits(POS)
# Deduplicate and cap to keep artifacts useful and API-free after acquisition.
def dedup(rows):
    seen=set(); out=[]
    for x in rows:
        k=(x['reference'],x['matched_probe'])
        if k not in seen: seen.add(k); out.append(x)
    return out
counter=dedup(counter); positive=dedup(positive)

verified=[r for r in records if r['status']=='verified_text']
# Argument map records evidence relationships without asserting a final theology.
argument_map={
 'question':'What does the Qur\'an itself say revelation is intended to produce in the human being?',
 'observed_clusters':[
   {'cluster':'guidance','evidence_ids':[r['id'] for r in verified if r['reference'] in ['2:2','2:185','5:15','5:16','10:57','14:1','16:89','17:9']]},
   {'cluster':'heart/soul transformation','evidence_ids':[r['id'] for r in verified if r['reference'] in ['10:57','39:23','57:16','91:9']]},
   {'cluster':'embodied ethical effect','evidence_ids':[r['id'] for r in verified if r['reference'] in ['29:45','62:2']]}
 ],
 'counter_evidence_probe_count':len(counter),
 'status':'research_synthesis_not_final_verdict'
}

# Bounded draft: every paragraph names its evidence; it avoids claiming that
# the selected verses alone exhaust the Quranic answer.
lines=[]
lines.append('# الفصل ٠١ — مسودة بحثية مضبوطة')
lines.append('')
lines.append('> الحالة: مسودة بحثية آلية. لا تمثل حكمًا نهائيًا، ولا تدّعي استنفاد القرآن في سؤالها.')
lines.append('')
lines.append('## السؤال')
lines.append(argument_map['question'])
lines.append('')
lines.append('## ما تثبته المادة النصية في هذه الجولة')
for cluster in argument_map['observed_clusters']:
    refs=[next(r['reference'] for r in verified if r['id']==eid) for eid in cluster['evidence_ids']]
    if refs: lines.append(f"- يظهر محور **{cluster['cluster']}** في هذه العينة من المواضع: {', '.join(refs)}. هذا وصف لمواضع النص، وليس حكمًا بأن هذه الآيات وحدها تحسم البنية الكاملة للمشروع.")
lines.append('')
lines.append('## شرط عدم التسرع')
lines.append(f'- تم فحص {len(verified)} موضعًا نصيًا بالمقارنة مع مصدر ثانٍ مستقل (Quranpedia/Hafs).')
lines.append(f'- جرى تشغيل بحث مضاد مع {len(counter)} نتيجة على مؤشرات لغوية تتصل بالضلال والظلم والقسوة والغفلة والنفاق والإعراض والكذب.')
lines.append('- نتائج البحث المضاد ليست «تفنيدًا» تلقائيًا؛ هي قائمة فحص تمنع انتقاء الشواهد المؤيدة فقط.')
lines.append('')
lines.append('## ما لم يُحسم')
lines.append('- العلاقة بين هذه الآيات وبين «غاية الوحي» تحتاج مقارنة تفسيرية أوسع، ودراسة السياقات، وتحديد درجة الاتفاق والخلاف بين المفسرين.')
lines.append('- لا يجوز تحويل تكرار محور لغوي إلى نظرية كلية عن الإسلام دون استقراء أوسع ومراجعة نقدية.')
lines.append('')
lines.append('## قرار البوابة')
lines.append('الانتقال إلى الكتابة النهائية محجوب حتى يكتمل الاستقراء المقارن للأدلة والتفسيرات ويُختبر ضد الاعتراضات.')

artifact={'run_at':datetime.now(timezone.utc).isoformat(),'source':{'name':'Tanzil','url':tanzil_url,'sha256':sha},
          'cross_source':'Quranpedia Hafs API','refs':REFS,'verified_text_count':len(verified),'records':records,
          'positive_lexical_scan':positive[:500],'counter_evidence_scan':counter[:500],
          'argument_map':argument_map,'draft_status':'BOUNDED_RESEARCH_DRAFT','draft':'\n'.join(lines)}
(DATA/'chapter_01_autonomous_research.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DATA/'chapter_01_research_draft.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

print(json.dumps({'status':'PASS' if len(verified)==len(REFS) else 'BLOCKED','verified_text_count':len(verified),'counter_scan':len(counter),'artifact':'book/research_data/chapter_01_autonomous_research.json'},ensure_ascii=False))
if len(verified)!=len(REFS): raise SystemExit(2)
