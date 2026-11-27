from dataclasses import dataclass
import unittest

@dataclass(frozen=True)
class Work:
 id: str
 benefit: int
 effort: int
 authorized: bool
 ready: bool
 risk: int = 0
 completed: bool = False
 verified: bool = False

def next_work(items):
 eligible=[w for w in items if w.authorized and w.ready and w.verified and not w.completed and w.risk==0 and w.benefit>0 and w.effort>0]
 return min(eligible,key=lambda w:(-w.benefit/w.effort,-w.benefit,w.id),default=None)

def execute_bounded(items,execute,limit=5):
 remaining=list(items); results={}
 for _ in range(limit):
  w=next_work(remaining)
  if w is None: break
  remaining=[x for x in remaining if x.id!=w.id]
  try: results[w.id]='PASS' if execute(w) is True else 'FAIL'
  except Exception: results[w.id]='FAIL'
 return results

class InitiativeTests(unittest.TestCase):
 def test_priority_and_boundaries(self):
  items=[Work('useful',8,2,True,True,verified=True),Work('slow',9,9,True,True,verified=True),Work('unsafe',100,1,True,True,1,verified=True),Work('unapproved',100,1,False,True,verified=True),Work('done',100,1,True,True,completed=True,verified=True),Work('unknown',100,1,True,True)]
  self.assertEqual(next_work(items).id,'useful')
  self.assertEqual(execute_bounded(items,lambda w:w.id!='useful'),{'useful':'FAIL','slow':'PASS'})
  self.assertIsNone(next_work(items[2:]))
  self.assertEqual(len(execute_bounded(items,lambda w:True,1)),1)
