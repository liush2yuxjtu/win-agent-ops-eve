import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, redact
from rules import diagnose, family

class OpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.store=Store(self.root/'ops.sqlite');self.source=self.root/'status.json';self.now=time.time()
    def tearDown(self): self.tmp.cleanup()
    def refresh(self,checks,hb=None,**extra):
        self.source.write_text(json.dumps({'heartbeat':hb if hb is not None else self.now,'checks':checks,**extra}))
        return self.store.refresh(self.source,self.now)
    def test_idempotent_import_and_restart(self):
        self.refresh({'x.auth':{'status':'fail','detail':'login-401'}})
        self.store.refresh(self.source,self.now)
        self.assertEqual(self.store.state()['metrics']['events'],2) # auth plus missing delivery status
        self.assertEqual(len(Store(self.root/'ops.sqlite').issue('x.auth')['diagnoses']),1)
    def test_decision_does_not_repair(self):
        self.refresh({'x.auth':{'status':'fail','detail':'login-401'}})
        issue=self.store.issue('x.auth')
        body=dict(id='test-record-001',issue='x.auth',revision=issue['revision'],solution='auth-1',choice='adopt',note='只记录选择')
        self.store.record(body,'decision');self.store.record(body,'decision')
        self.assertEqual(self.store.issue('x.auth')['status'],'fail')
        self.assertEqual(self.store.state()['metrics']['decisions'],1)
        self.assertEqual(Store(self.root/'ops.sqlite').issue('x.auth')['decisions'][0]['choice'],'adopt')
        body['choice']='reject'
        with self.assertRaises(ValueError): self.store.record(body,'decision')
    def test_three_choices_and_outcomes_persist(self):
        self.refresh({'x.auth':{'status':'fail','detail':'login-401'}})
        rev=self.store.issue('x.auth')['revision']
        for index,choice in enumerate(('adopt','reject','defer')):
            self.store.record(dict(id=f'decision-{index}',issue='x.auth',revision=rev,solution='auth-1',choice=choice,note='验证记录'),'decision')
        self.store.record(dict(id='outcome-test',issue='x.auth',revision=rev,solution='auth-1',result='failed',note='人工验证失败'),'outcome')
        issue=Store(self.root/'ops.sqlite').issue('x.auth')
        self.assertEqual(len(issue['decisions']),3);self.assertEqual(issue['outcomes'][0]['result'],'failed')
        self.assertEqual(issue['status'],'fail')
    def test_version_rejects_stale_and_wrong_solution(self):
        self.refresh({'x.auth':{'status':'fail','detail':'login-401'}})
        rev=self.store.issue('x.auth')['revision']
        body=dict(id='wrong-solution',issue='x.auth',revision=rev,solution='owner-1',choice='adopt',note='')
        with self.assertRaises(ValueError): self.store.record(body,'decision')
        self.now+=30;self.refresh({'x.auth':{'status':'pass','detail':'ok'}})
        body['solution']='auth-1'
        with self.assertRaises(ValueError): self.store.record(body,'decision')
        self.assertEqual(len(self.store.issue('x.auth')['diagnoses']),2)
    def test_stale_pass_is_not_recovery(self):
        self.refresh({'x.auth':{'status':'pass','detail':'ok'}},hb=self.now-500)
        self.assertEqual(self.store.issue('x.auth')['status'],'unverified')
        self.assertEqual(self.store.issue('observer.freshness')['status'],'fail')
    def test_missing_item_not_recovered(self):
        self.refresh({'x.auth':{'status':'fail','detail':'401'}})
        self.now+=30;self.refresh({'other.http':{'status':'pass','detail':'ok'}})
        self.assertEqual(self.store.issue('x.auth')['status'],'unverified')
    def test_future_heartbeat_and_empty_checks(self):
        r=self.refresh({'x.auth':{'status':'pass','detail':'ok'}},hb=self.now+300)
        self.assertFalse(r['fresh'])
        r=self.refresh({});self.assertFalse(r['fresh'])
    def test_rollback_snapshot_and_malformed_source(self):
        self.refresh({'x.auth':{'status':'fail','detail':'401'}})
        r=self.refresh({'x.auth':{'status':'pass','detail':'ok'}},hb=self.now-20)
        self.assertFalse(r['fresh']);self.assertNotEqual(self.store.issue('x.auth')['status'],'pass')
        self.source.write_text('{');r=self.store.refresh(self.source,self.now)
        self.assertFalse(r['fresh'])
    def test_recovery_and_recurrence_keep_history(self):
        for status in ('fail','pass','fail'):
            self.now+=30;self.refresh({'x.auth':{'status':status,'detail':'401' if status=='fail' else 'ok'}})
        self.assertEqual(len(self.store.issue('x.auth')['events']),3)
    def test_owner_precondition_precedes_auth(self):
        self.assertEqual(family('jdaro.auth','backend-owner-invalid'),'owner')
        self.assertNotIn('凭据负责人',diagnose('jdaro.auth','unverified','backend-owner-invalid')['solutions'][0]['title'])
    def test_top_five_diverse_and_unknown_not_padded(self):
        for name in ('x.auth','x.backend.owner','x.loaded-version','x.clean','x.http','x.pin','observer.freshness','delivery.pipeline'):
            d=diagnose(name,'fail','error');s=d['solutions']
            self.assertEqual(len(s),5);self.assertEqual(len({v['title'] for v in s}),5)
            self.assertEqual([v['rank'] for v in s],[1,2,3,4,5])
        self.assertEqual(len(diagnose('new.sensor','fail','unexpected')['solutions']),2)
    def test_invalid_result_and_missing_evidence_rejected(self):
        self.refresh({'x.auth':{'status':'fail','detail':'401'}})
        body=dict(id='outcome-invalid',issue='x.auth',revision=self.store.issue('x.auth')['revision'],solution='auth-1',result='success',note='')
        with self.assertRaises(ValueError): self.store.record(body,'outcome')
    def test_backup_and_redaction(self):
        self.refresh({'x.auth':{'status':'fail','detail':'token=do-not-keep'}})
        self.assertNotIn('do-not-keep',self.store.issue('x.auth')['detail'])
        with sqlite3.connect(self.store.backup()) as c:self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertNotIn('secret-value',redact('Bearer secret-value'))
    def test_source_symlink_rejected(self):
        target=self.root/'target.json';target.write_text('{}');self.source.symlink_to(target)
        self.assertFalse(self.store.refresh(self.source,self.now)['fresh'])

if __name__=='__main__':unittest.main(verbosity=2)
