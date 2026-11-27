import tempfile, unittest
from pathlib import Path
from engine import Engine
class TestEngine(unittest.TestCase):
 def test_pipeline(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'product.txt'; calls=[]
   def produce(_):
    calls.append(1); p.write_text('42'); return str(p)
   def valid(x): return Path(x).is_file() and Path(x).read_text()=='42'
   def fail(_): raise ValueError('expected')
   tasks={'produce':([],1,produce,valid),'verify':(['produce'],1,lambda a:Path(a[0]).read_text(),lambda x:x=='42'),'fail':([],1,fail,bool),'blocked':(['fail'],1,lambda _:True,bool)}
   e=Engine(Path(d)/'state.db')
   expected={'produce':'PASS','verify':'PASS','fail':'FAIL','blocked':'BLOCKED'}
   self.assertEqual(e.run(tasks)[0],expected)
   self.assertEqual(e.run(tasks)[0],expected); self.assertEqual(len(calls),1)
   p.unlink(); self.assertEqual(e.run(tasks)[0],expected); self.assertEqual(len(calls),2)
   e.db.close()
if __name__=='__main__': unittest.main()
