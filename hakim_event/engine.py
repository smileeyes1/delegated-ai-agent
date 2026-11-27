import sqlite3, hashlib, json
from pathlib import Path

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Engine:
 def __init__(self, db):
  self.db=sqlite3.connect(db)
  self.db.execute('CREATE TABLE IF NOT EXISTS results (id TEXT PRIMARY KEY, fingerprint TEXT, state TEXT, output TEXT)')
 def run(self,tasks):
  pending=dict(tasks); done={}; outputs={}
  while pending:
   ready=[k for k,(deps,version,fn,validate) in pending.items() if all(d in done for d in deps)]
   if not ready: break
   for k in ready:
    deps,version,fn,validate=pending.pop(k)
    if any(done[d]!='PASS' for d in deps): done[k]='BLOCKED'; continue
    args=[outputs[d] for d in deps]
    fp=hashlib.sha256(json.dumps([version,args],sort_keys=True).encode()).hexdigest()
    row=self.db.execute('SELECT fingerprint,state,output FROM results WHERE id=?',(k,)).fetchone()
    try:
     cached=json.loads(row[2]) if row and row[:2]==(fp,'PASS') else None
     if cached is not None and validate(cached): out=cached
     else:
      out=fn(args)
      if not validate(out): raise ValueError('output validation failed')
     state='PASS'; outputs[k]=out
    except Exception as e: state='FAIL'; out=str(e)
    with self.db: self.db.execute('INSERT OR REPLACE INTO results VALUES (?,?,?,?)',(k,fp,state,json.dumps(out,ensure_ascii=False)))
    done[k]=state
  done.update({k:'BLOCKED' for k in pending}); return done,outputs
