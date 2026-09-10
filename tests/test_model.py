import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from model import evidence_packet

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'ops.sqlite')
        self.source = self.root / 'status.json'
        self.now = time.time()
        self.refresh('fail', '401')
        self.packet = evidence_packet(self.store, 'x.auth')
        self.analysis = dict(self.store.state()['issues'][0]['analysis'])
        self.analysis['solutions'] = [dict(self.analysis['solutions'][0], id='model-choice')]
        self.report = {'issue': 'x.auth', 'revision': self.packet['revision'], 'sessionId': 'test-session', 'diagnosis': self.analysis}
    def tearDown(self):
        self.tmp.cleanup()
    def refresh(self, status, detail):
        self.source.write_text(json.dumps({'heartbeat': self.now, 'checks': {'x.auth': {'status': status, 'detail': detail}}, 'deliveryError': None}))
        self.store.refresh(self.source, self.now)
    def finish(self):
        self.store.begin_model_run('run-001', self.packet)
        self.store.finish_model_run('run-001', report=self.report)
    def current(self):
        return next(i for i in self.store.state()['issues'] if i['id'] == 'x.auth')
    def test_model_survives_refresh_and_restart(self):
        self.finish()
        revision = self.current()['revision']
        self.now += 30
        self.refresh('fail', '401')
        self.assertEqual(self.current()['revision'], revision)
        self.assertEqual(Store(self.store.path).model_run('run-001')['state'], 'completed')
        self.assertEqual(len(self.store.issue('x.auth')['diagnoses']), 2)
    def test_model_decision_and_feedback(self):
        self.finish()
        body = dict(id='decision-model-1', issue='x.auth', revision=self.current()['revision'], solution='model-choice', choice='adopt', note='只记录')
        self.store.record(body, 'decision')
        self.store.record(dict(body, id='outcome-model-1', result='failed', note='未解决'), 'outcome')
        packet = evidence_packet(self.store, 'x.auth')
        feedback = next(e for e in packet['evidence'] if e['kind'] == 'human-feedback')
        self.assertEqual(feedback['content']['solution']['id'], 'model-choice')
        self.assertEqual(self.current()['status'], 'fail')
    def test_changed_evidence_hides_old_model_not_history(self):
        self.finish()
        revision = self.current()['revision']
        self.now += 30
        self.refresh('pass', 'ok')
        self.assertNotEqual(self.current()['revision'], revision)
        with self.assertRaises(ValueError):
            self.store.record(dict(id='decision-stale-1', issue='x.auth', revision=revision, solution='model-choice', choice='adopt', note=''), 'decision')
        self.assertEqual(len(self.store.issue('x.auth')['diagnoses']), 3)
    def test_failed_model_has_no_fake_diagnosis(self):
        self.store.begin_model_run('run-001', self.packet)
        self.store.finish_model_run('run-001', error='CPA unavailable')
        self.assertEqual(len(self.store.issue('x.auth')['diagnoses']), 1)
        self.assertEqual(self.store.model_run('run-001')['state'], 'failed')
    def test_one_active_run_and_wrong_revision(self):
        self.store.begin_model_run('run-001', self.packet)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.begin_model_run('run-002', self.packet)
        with self.assertRaises(ValueError):
            self.store.finish_model_run('run-001', report=dict(self.report, revision='wrong'))
    def test_sibling_evidence_invalidates_model(self):
        self.finish()
        self.now += 30
        self.source.write_text(json.dumps({'heartbeat': self.now, 'checks': {'x.auth': {'status': 'fail', 'detail': '401'}, 'x.owner': {'status': 'fail', 'detail': 'mismatch'}}, 'deliveryError': None}))
        self.store.refresh(self.source, self.now)
        self.assertEqual(self.current()['analysis']['engine'], 'rules-1')
        self.assertEqual(len(self.store.issue('x.auth')['events']), 1)

    def test_quality_counts_feedback_without_claiming_accuracy(self):
        self.report['audience']='leadership-v1'
        self.report['diagnosis']['hiddenIssues']=[{'title':'候选','reason':'待核实','evidenceIds':['current-issue']}]
        self.finish()
        issue=self.current()
        self.assertEqual(issue['analysis']['audience'],'leadership-v1')
        self.store.record(dict(id='feedback-quality-1',issue='x.auth',revision=issue['revision'],solution='model-choice',result='recurred',note='人工反馈仍待核实'),'outcome')
        quality=self.store.quality()
        self.assertFalse(quality['qualityMeasured'])
        self.assertEqual(quality['outcomes']['recurred'],1)
        self.assertEqual(quality['firstRecommendationFeedback'],1)
        self.assertEqual(quality['hiddenCandidates'][0]['issue'],'x.auth')

    def test_packet_distinguishes_cached_monitor_from_live_probe(self):
        current=self.packet['evidence'][0]
        self.assertEqual(current['kind'],'stored-monitor-result-not-fresh-probe')
        self.assertIn('不是本次实际登录时间',current['content']['observationSemantics'])

    def test_late_completion_preserves_new_source(self):
        self.store.begin_model_run('run-001', self.packet)
        self.now += 30
        self.refresh('pass', 'ok')
        self.store.finish_model_run('run-001', report=self.report)
        self.assertEqual(self.current()['analysis']['engine'], 'rules-1')
        self.assertEqual(self.store.model_run('run-001')['state'], 'completed')

if __name__ == '__main__':
    unittest.main(verbosity=2)
