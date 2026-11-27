from pathlib import Path
import hashlib
from test_initiative import Work, execute_bounded
from test_math_product import questions, render, eastern

def main():
 out=Path('delivery'); out.mkdir(exist_ok=True)
 q=questions()
 assert len(q)==6 and all(x['n']==10*x['tens']+x['ones'] for x in q)
 # In RTL, put ones at the right of tens.
 worksheet=render(q).replace('<th>العدد</th><th>العشرات</th><th>الآحاد</th>','<th>العدد</th><th>الآحاد</th><th>العشرات</th>')
 key='<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>مفتاح التصحيح</title><h1>مفتاح التصحيح للمعلم</h1>'+''.join('<p>'+eastern(x['n'])+' : '+eastern(x['ones'])+' آحاد، '+eastern(x['tens'])+' عشرات</p>' for x in q)+'</html>'
 products={'math.html':worksheet,'teacher-key.html':key}
 def execute(w):
  p=out/w.id; p.write_text(products[w.id],encoding='utf-8')
  assert p.read_text(encoding='utf-8')==products[w.id]
  p.with_suffix('.sha256').write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
  return True
 result=execute_bounded([Work('math.html',8,1,True,True,verified=True),Work('teacher-key.html',6,1,True,True,verified=True)],execute)
 assert result=={'math.html':'PASS','teacher-key.html':'PASS'},result
 print(result)
if __name__=='__main__': main()
