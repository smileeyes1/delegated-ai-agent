import tempfile, unittest, json, hashlib
from pathlib import Path
from engine import Engine

def eastern(n): return str(n).translate(str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'))
def questions():
 return [{'n':n,'tens':n//10,'ones':n%10} for n in (24,37,50,68,91,99)]
def render(q):
 rows=''.join('<tr><td>'+eastern(x['n'])+'</td><td></td><td></td></tr>' for x in q)
 return '<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>القيمة المنزلية</title><style>body{font:24px sans-serif;padding:1rem}table{border-collapse:collapse;width:100%}td,th{border:1px solid;padding:1rem;text-align:center}</style><h1>القيمة المنزلية</h1><p>أكتب عدد العشرات والآحاد.</p><table><tr><th>العدد</th><th>العشرات</th><th>الآحاد</th></tr>'+rows+'</table></html>'
class ProductTest(unittest.TestCase):
 def test_product(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'math.html'
   def produce(a):
    p.write_text(render(a[0]),encoding='utf-8')
    return {'path':str(p),'sha':hashlib.sha256(p.read_bytes()).hexdigest()}
   def valid(x):
    f=Path(x['path'])
    return f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==x['sha'] and f.read_text(encoding='utf-8')==render(questions())
   e=Engine(Path(d)/'state.db')
   tasks={'questions':([],1,lambda _:questions(),lambda q:len(q)==6 and all(x['n']==10*x['tens']+x['ones'] for x in q)), 'worksheet':(['questions'],1,produce,valid)}
   self.assertEqual(e.run(tasks)[0],{'questions':'PASS','worksheet':'PASS'})
   self.assertTrue(p.exists())
   e.db.close()
if __name__=='__main__': unittest.main()
