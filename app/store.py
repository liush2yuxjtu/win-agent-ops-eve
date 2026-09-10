import hashlib
from contextlib import contextmanager, closing
import json
import math
import os
import re
import sqlite3
import time
from pathlib import Path
from rules import diagnose, VERSION

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home()/'.local/state/win-agent-os/legacy-monitor/status.json'
HISTORY = ROOT/'history.sqlite'
DB = ROOT/'data/ops.sqlite'
STALE_SECONDS = 300

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()

def redact(text):
    text = re.sub(r'(?i)(bearer\s+)[\w.\-/+=]+', r'\1[已脱敏]', str(text))
    return re.sub(r'(?i)((?:password|token|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+', r'\1[已脱敏]', text)

class Store:
    def __init__(self, path=DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY, observed REAL NOT NULL, imported REAL NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS issues(id TEXT PRIMARY KEY, status TEXT NOT NULL, detail TEXT NOT NULL, first_seen REAL NOT NULL, last_seen REAL NOT NULL, revision TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS diagnoses(id TEXT PRIMARY KEY, issue TEXT NOT NULL REFERENCES issues(id), created REAL NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, issue TEXT NOT NULL REFERENCES issues(id), at REAL NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL, snapshot TEXT NOT NULL REFERENCES snapshots(id));
            CREATE TABLE IF NOT EXISTS source_events(id TEXT PRIMARY KEY, at TEXT NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY, issue TEXT NOT NULL REFERENCES issues(id), revision TEXT NOT NULL REFERENCES diagnoses(id), solution TEXT NOT NULL, choice TEXT NOT NULL, note TEXT NOT NULL, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS outcomes(id TEXT PRIMARY KEY, issue TEXT NOT NULL REFERENCES issues(id), revision TEXT NOT NULL REFERENCES diagnoses(id), solution TEXT NOT NULL, result TEXT NOT NULL, note TEXT NOT NULL, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY, issue TEXT NOT NULL REFERENCES issues(id), source_revision TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('running','completed','failed')), started REAL NOT NULL, finished REAL, packet TEXT NOT NULL, report TEXT, error TEXT);
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_model_run ON model_runs(issue) WHERE state='running';
            PRAGMA user_version=2;
            ''')
        os.chmod(self.path,0o600)

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path, timeout=10)
        try:
            c.row_factory = sqlite3.Row
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('PRAGMA busy_timeout=10000')
            with c:
                yield c
        finally:
            c.close()

    def refresh(self, source=SOURCE, now=None):
        now = time.time() if now is None else now
        error = None
        try:
            if source.is_symlink() or source.stat().st_size > 2_000_000:
                raise ValueError('源文件为软链接或超过 2 MB')
            data = json.loads(source.read_text())
            checks = data['checks']
            hb = data['heartbeat']
            if not isinstance(hb,(int,float)) or isinstance(hb,bool) or not math.isfinite(hb) or hb <= 0 or hb > now+60:
                raise ValueError('心跳时间无效或超前')
            if not isinstance(checks,dict) or not checks or len(checks)>500:
                raise ValueError('checks 缺失、为空或过大')
            normalized = {}
            for key,value in checks.items():
                if not isinstance(key,str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,120}',key) or not isinstance(value,dict):
                    raise ValueError('检查项结构无效')
                if key.startswith(('observer.','delivery.')): raise ValueError('源使用了保留检查项')
                status=value.get('status')
                if status not in ('pass','fail','unverified'): raise ValueError('未知检查状态')
                normalized[key]={'status':status,'detail':redact(value.get('detail',''))[:2000]}
            events=data.get('events',[])
            if not isinstance(events,list): raise ValueError('事件结构无效')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            error=type(exc).__name__ + ': ' + str(exc)[:180]
            normalized={}; hb=now; data={}; events=[]
        with self.connect() as c:
            previous=c.execute("SELECT value FROM meta WHERE key='heartbeat'").fetchone()
            old_hb=float(previous['value']) if previous else 0
            if not error and hb<old_hb:
                error='源心跳倒退；保留旧证据，不接受回滚快照'
                normalized={}; events=[]
            age=max(0,now-hb)
            fresh=not error and age <= STALE_SECONDS
            checks=dict(normalized)
            for old in c.execute("SELECT id FROM issues WHERE id NOT LIKE 'observer.%' AND id NOT LIKE 'delivery.%'"):
                if old['id'] not in checks:
                    checks[old['id']]={'status':'unverified','detail':'当前采样缺失；不得推断恢复'}
            if error or not fresh:
                checks={k:{'status':'unverified','detail':f"证据不可用于当前判断；上次信号 {v['status']}: {v['detail']}"} for k,v in checks.items()}
            checks['observer.freshness']={'status':'fail' if error or not fresh else 'pass','detail':error or ('心跳过期；需核对原观察者' if not fresh else 'ok')}
            checks['delivery.pipeline']={'status':'fail' if data.get('deliveryError') else ('pass' if fresh and 'deliveryError' in data else 'unverified'),'detail':redact(data.get('deliveryError') or ('ok' if fresh and 'deliveryError' in data else '当前采样未提供投递状态'))[:2000]}
            snapshot={'heartbeat':hb,'checks':checks,'source':str(source),'error':error}
            sid=digest(snapshot)
            c.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?)',(sid,hb,now,encode(snapshot)))
            context_revision=digest(checks)
            for key,value in sorted(checks.items()):
                old=c.execute('SELECT * FROM issues WHERE id=?',(key,)).fetchone()
                if value['status']=='pass' and old is None: continue
                status,detail=value['status'],value['detail']
                analysis=diagnose(key,status,detail)
                analysis['evidence']={'snapshot':sid,'check':key,'status':status,'detail':detail}
                revision=digest([key,status,detail,VERSION,context_revision])
                changed=old is None or (old['status'],old['detail'])!=(status,detail)
                c.execute('INSERT INTO issues VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status, detail=excluded.detail,last_seen=excluded.last_seen,revision=excluded.revision',
                          (key,status,detail,hb if key in normalized else now,hb if key in normalized else now,revision))
                c.execute('INSERT OR IGNORE INTO diagnoses VALUES(?,?,?,?)',(revision,key,now,encode(analysis)))
                if changed:
                    c.execute('INSERT INTO events(issue,at,status,detail,snapshot) VALUES(?,?,?,?,?)',(key,now,status,detail,sid))
            for e in events[:200]:
                if isinstance(e,dict) and isinstance(e.get('id'),str):
                    c.execute('INSERT OR IGNORE INTO source_events VALUES(?,?,?)',(e['id'][:200],str(e.get('at',''))[:100],redact(e.get('body',''))[:12000]))
            meta={'refreshed':now,'source':str(source),'fresh':fresh,'sourceError':error,'age':age,'engine':VERSION}
            if not error: c.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('heartbeat',str(hb)))
            c.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('collector',encode(meta)))
        return meta

    def state(self):
        with self.connect() as c:
            row=c.execute("SELECT value FROM meta WHERE key='collector'").fetchone()
            issues=[]
            for r in c.execute('SELECT issues.*,diagnoses.body FROM issues JOIN diagnoses ON diagnoses.id=issues.revision ORDER BY issues.id'):
                value=dict(r); value['analysis']=json.loads(value.pop('body'))
                model=c.execute("SELECT id,body FROM diagnoses WHERE issue=? AND json_extract(body,'$.sourceRevision')=? ORDER BY created DESC LIMIT 1",(r['id'],r['revision'])).fetchone()
                value['sourceRevision']=r['revision']
                if model:
                    value['revision']=model['id']; value['analysis']=json.loads(model['body'])
                issues.append(value)
            issues.sort(key=lambda x:(x['status']=='pass',x['analysis']['priority'],x['id']))
            return {'collector':json.loads(row['value']) if row else {},'issues':issues,
                    'metrics':{'events':c.execute('SELECT count(*) FROM events').fetchone()[0],
                    'decisions':c.execute('SELECT count(*) FROM decisions').fetchone()[0],
                    'outcomes':c.execute('SELECT count(*) FROM outcomes').fetchone()[0],
                    'sourceEvents':c.execute('SELECT count(*) FROM source_events').fetchone()[0],
                    'quality':'尚无独立标注事故集；不报告真实 Top 1 命中率或 Top 5 覆盖率。'}}

    def issue(self,key):
        with self.connect() as c:
            row=c.execute('SELECT * FROM issues WHERE id=?',(key,)).fetchone()
            if not row: raise KeyError('问题不存在')
            result=dict(row)
            result['diagnoses']=[dict(r) for r in c.execute('SELECT * FROM diagnoses WHERE issue=? ORDER BY created DESC',(key,))]
            for r in result['diagnoses']: r['body']=json.loads(r['body'])
            for table in ('events','decisions','outcomes'):
                result[table]=[dict(r) for r in c.execute(f'SELECT * FROM {table} WHERE issue=? ORDER BY at DESC LIMIT 300',(key,))]
            return result

    def record(self,body,kind):
        table='decisions' if kind=='decision' else 'outcomes'
        field='choice' if kind=='decision' else 'result'
        allowed=('adopt','reject','defer') if kind=='decision' else ('success','failed','recurred','unverified')
        for name in ('id','issue','revision','solution',field,'note'):
            if not isinstance(body.get(name),str): raise ValueError('记录字段缺失')
        if not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',body['id']) or body[field] not in allowed or len(body['note'])>2000: raise ValueError('记录字段无效')
        if kind=='outcome' and not body['note'].strip(): raise ValueError('处理结果必须附说明或验证证据')
        with self.connect() as c:
            old=c.execute(f'SELECT * FROM {table} WHERE id=?',(body['id'],)).fetchone()
            values=(body['id'],body['issue'],body['revision'],body['solution'],body[field],redact(body['note']),time.time())
            if old:
                if tuple(old)[:6]!=values[:6]: raise ValueError('幂等 ID 与原记录内容冲突')
                return {'saved':True,'duplicate':True}
            row=c.execute('SELECT revision FROM issues WHERE id=?',(body['issue'],)).fetchone()
            analysis=c.execute('SELECT body FROM diagnoses WHERE id=? AND issue=?',(body['revision'],body['issue'])).fetchone()
            if not row or not analysis: raise ValueError('诊断不存在或不属于此问题')
            parsed=json.loads(analysis['body'])
            if row['revision']!=parsed.get('sourceRevision',body['revision']): raise ValueError('证据版本已变化，请刷新后重新选择')
            if body['solution'] not in [s['id'] for s in parsed['solutions']]: raise ValueError('方案不属于此诊断版本')
            c.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?,?,?)',values)
        return {'saved':True,'executed':False}

    def search(self,query):
        query=query.strip()[:120]
        if not query: return []
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        with self.connect() as c:
            rows=[{'kind':'红灯事件','id':str(r['id']),'text':r['body']} for r in c.execute("SELECT * FROM source_events WHERE body LIKE ? ESCAPE '\\' ORDER BY at DESC LIMIT 15",('%'+escaped+'%',))]
        if HISTORY.exists():
            with closing(sqlite3.connect(f'file:{HISTORY}?mode=ro',uri=True,timeout=5)) as c:
                # FTS query is quoted data, never user-supplied operators.
                q='"'+query.replace('"','""')+'"'
                for kind,key,text in c.execute('SELECT kind,id,snippet(search,2,\'\',\'\',\' … \',45) FROM search WHERE search MATCH ? LIMIT 15',(q,)):
                    rows.append({'kind':kind,'id':key,'text':redact(text)[:4000]})
        return rows[:30]

    def begin_model_run(self, run_id, packet):
        with self.connect() as c:
            c.execute("UPDATE model_runs SET state='failed',finished=?,error='诊断进程超时或中断；可重试' WHERE state='running' AND started<?",(time.time(),time.time()-240))
            c.execute("INSERT INTO model_runs(id,issue,source_revision,state,started,packet) VALUES(?,?,?,'running',?,?)",(run_id,packet['issue'],packet['revision'],time.time(),encode(packet)))

    def finish_model_run(self, run_id, report=None, error=None):
        with self.connect() as c:
            run=c.execute('SELECT * FROM model_runs WHERE id=?',(run_id,)).fetchone()
            if not run or run['state']!='running': raise ValueError('诊断运行已结束或不存在')
            if error:
                c.execute("UPDATE model_runs SET state='failed',finished=?,error=? WHERE id=?",(time.time(),redact(error)[:1000],run_id))
                return
            if report['issue']!=run['issue'] or report['revision']!=run['source_revision']: raise ValueError('诊断证据版本不匹配')
            analysis=dict(report['diagnosis'],engine='eve-cpa-1',family='model',sourceRevision=run['source_revision'],runId=run_id,sessionId=report['sessionId'],variant=report.get('variant','baseline'),audience=report.get('audience','technical'),authoredPromptHash=report.get('authoredPromptHash'))
            revision=digest([run_id,analysis])
            c.execute('INSERT INTO diagnoses VALUES(?,?,?,?)',(revision,run['issue'],time.time(),encode(analysis)))
            c.execute("UPDATE model_runs SET state='completed',finished=?,report=? WHERE id=?",(time.time(),encode(dict(report,diagnosisRevision=revision)),run_id))

    def model_run(self, run_id):
        with self.connect() as c:
            row=c.execute('SELECT id,issue,state,started,finished,error,report FROM model_runs WHERE id=?',(run_id,)).fetchone()
            if not row: raise KeyError('诊断运行不存在')
            result=dict(row)
            if result['report']: result['report']=json.loads(result['report'])
            return result

    def quality(self):
        state=self.state()
        candidates=[]
        for issue in state['issues']:
            for item in issue['analysis'].get('hiddenIssues',[]):
                candidates.append(dict(item,issue=issue['id'],revision=issue['revision']))
        with self.connect() as c:
            runs={r['state']:r['total'] for r in c.execute('SELECT state,count(*) total FROM model_runs GROUP BY state')}
            outcomes={r['result']:r['total'] for r in c.execute('SELECT result,count(*) total FROM outcomes GROUP BY result')}
            first=c.execute("SELECT count(*) FROM outcomes o JOIN diagnoses d ON d.id=o.revision WHERE o.solution=json_extract(d.body,'$.solutions[0].id')").fetchone()[0]
        return {'runs':runs,'outcomes':outcomes,'firstRecommendationFeedback':first,'hiddenCandidates':candidates,
                'qualityMeasured':False,'note':'反馈数量不是准确率。尚无独立标注事故集，不报告命中率、漏报率或覆盖率。'}

    def backup(self):
        target=self.path.parent/'ops.backup.sqlite'
        with self.connect() as source, closing(sqlite3.connect(target)) as dest:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise RuntimeError('备份完整性检查失败')
        os.chmod(target,0o600)
        return target
