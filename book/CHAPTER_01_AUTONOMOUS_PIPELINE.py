"""Evidence-controlled autonomous pipeline for Chapter 01.

Acquires primary Quran text from Tanzil, cross-checks against Quranpedia's
Hafs API using an explicit orthography-normalization layer, retrieves tafsir,
collects counter-evidence, and emits an auditable evidence map and bounded
research draft. Exact source text is preserved; normalization is used only
for cross-source equivalence testing.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, json, re
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'research_data'; DATA.mkdir(exist_ok=True)
BASE='https://api.quranpedia.net/v1'
UA='BOOK_FACTORY/1.1 (evidence research runner)'
REFS=['2:2','2:185','5:15','5:16','10:57','14:1','16:89','17:9','29:45','39:23','57:16','62:2','91:9']
POS={'هدى':'guidance','تزكية':'purification','ذكر':'remembrance','تقوى':'taqwa','رحمة':'mercy','إصلاح':'reform','عدل':'justice','إحسان':'excellence','عباد':'worship/service','صلو':'prayer'}
COUNTER={'ضلال':'misguidance','ظلم':'wrongdoing','قسو':'hardness','غفل':'heedlessness','نفاق':'hypocrisy','إعراض':'turning-away','كذب':'denial/lying'}

def get(url):
    r=urlopen(Request(url,headers={'User-Agent':UA}),timeout=30)
    return r.read(),r.headers.get('content-type','')

def norm(s):
    s=s or ''
    s=s.replace('\ufeff','')
    s=re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]','',s)
    s=s.translate(str.maketrans({'ٱ':'ا','أ':'ا','إ':'ا','آ':'ا','ى':'ي','ة':'ة'}))
    return re.sub(r'\s+','',s)

def load_tanzil():
    url='https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true&marks=true&sajdah=true&rub=true&stanween=true'
    b,_=get(url); text=b.decode('utf-8-sig')
    (DATA/'tanzil-uthmani.txt').write_text(text,encoding='utf-8')
    verses={}
    for line in text.splitlines():
        p=line.split('|',2)
        if len(p)==3: verses[f'{p[0]}:{p[1]}']=p[2].strip()
    return verses,hashlib.sha256(b).hexdigest(),url

def qpedia(ref):
    s,a=map(int,ref.split(':')); b,_=get(f'{BASE}/mushafs/1/{s}/{a}'); return json.loads(b)

def tafsir(ref,book=1):
    s,a=map(int,ref.split(':')); b,_=get(f'{BASE}/ayah/{s}/{a}/book/{book}'); return json.loads(b)

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

verses,sha,tanzil_url=load_tanzil()
missing=[r for r in REFS if r not in verses]
if missing: raise SystemExit(f'Missing primary text: {missing}')
records=[]
for ref in REFS:
    q=qpedia(ref); qraw=q.get('text',''); traw=verses[ref]; same=norm(qraw)==norm(traw)
    try: tf=tafsir(ref,1)
    except Exception as e: tf={'error':str(e)}
    records.append({'id':'Q01-'+ref.replace(':','-'),'reference':ref,'primary_text':traw,'quranpedia_text':qraw,
                    'text_crosscheck':'MATCH' if same else 'MISMATCH','crosscheck_method':'orthography_normalized_exact',
                    'context':nearby(ref,verses),'tafsir_book':tf.get('book',{}),'tafsir_content':tf.get('content',[]),
                    'status':'verified_text' if same else 'BLOCKED_TEXT_MISMATCH'})

all_text='\n'.join(f'{k}|{v}' for k,v in verses.items())
verified=[r for r in records if r['status']=='verified_text']
counter=hits(COUNTER,all_text); positive=hits(POS,all_text)
argument_map={'question':"What does the Qur'an itself say revelation is intended to produce in the human being?",
 'observed_clusters':[{'cluster':'guidance','evidence_ids':[r['id'] for r in verified if r['reference'] in ['2:2','2:185','5:15','5:16','10:57','14:1','16:89','17:9']]},
 {'cluster':'heart/soul transformation','evidence_ids':[r['id'] for r in verified if r['reference'] in ['10:57','39:23','57:16','91:9']]},
 {'cluster':'embodied ethical effect','evidence_ids':[r['id'] for r in verified if r['reference'] in ['29:45','62:2']]}],
 'counter_evidence_probe_count':len(counter),'status':'research_synthesis_not_final_verdict'}
lines=['# الفصل ٠١ — مسودة بحثية مضبوطة','', '> الحالة: مسودة بحثية آلية. لا تمثل حكمًا نهائيًا، ولا تدّعي استنفاد القرآن في سؤالها.','', '## السؤال',argument_map['question'],'', '## ما تثبته المادة النصية في هذه الجولة']
for cluster in argument_map['observed_clusters']:
    refs=[next(r['reference'] for r in verified if r['id']==eid) for eid in cluster['evidence_ids']]
    if refs: lines.append(f"- يظهر محور **{cluster['cluster']}** في هذه العينة من المواضع: {', '.join(refs)}. هذا وصف لمواضع النص، وليس حكمًا بأن هذه الآيات وحدها تحسم البنية الكاملة للمشروع.")
lines += ['', '## شرط عدم التسرع',f'- تم فحص {len(verified)} موضعًا نصيًا بالمقارنة مع مصدر ثانٍ مستقل (Quranpedia/Hafs) بعد تطبيع اختلافات الرسم والعلامات فقط.',f'- جرى تشغيل بحث مضاد مع {len(counter)} نتيجة على مؤشرات لغوية مضادة.', '- نتائج البحث المضاد ليست تفنيدًا تلقائيًا؛ هي قائمة فحص تمنع انتقاء الشواهد المؤيدة فقط.','', '## ما لم يُحسم','- العلاقة بين هذه الآيات وبين غاية الوحي تحتاج مقارنة تفسيرية أوسع ودراسة السياقات وتحديد درجة الاتفاق والخلاف بين المفسرين.','- لا يجوز تحويل تكرار محور لغوي إلى نظرية كلية عن الإسلام دون استقراء أوسع ومراجعة نقدية.','', '## قرار البوابة','الانتقال إلى الكتابة النهائية محجوب حتى يكتمل الاستقراء المقارن للأدلة والتفسيرات ويُختبر ضد الاعتراضات.']
artifact={'run_at':datetime.now(timezone.utc).isoformat(),'source':{'name':'Tanzil','url':tanzil_url,'sha256':sha},'cross_source':'Quranpedia Hafs API','refs':REFS,'verified_text_count':len(verified),'records':records,'positive_lexical_scan':positive[:500],'counter_evidence_scan':counter[:500],'argument_map':argument_map,'draft_status':'BOUNDED_RESEARCH_DRAFT','draft':'\n'.join(lines)}
(DATA/'chapter_01_autonomous_research.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DATA/'chapter_01_research_draft.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS' if len(verified)==len(REFS) else 'BLOCKED','verified_text_count':len(verified),'counter_scan':len(counter)},ensure_ascii=False))
if len(verified)!=len(REFS): raise SystemExit(2)
