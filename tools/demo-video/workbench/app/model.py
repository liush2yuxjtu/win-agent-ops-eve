"""Evidence packets and an SSH client. CPA credentials never leave Mac mini."""
import json
import subprocess
from store import encode, redact


def evidence_packet(store, key, question='解释这个问题，比较根因并给出最多五个互补方案。'):
    issue = store.issue(key)
    evidence = [{'evidenceId': 'current-issue', 'kind': 'current', 'content': {
        name: issue[name] for name in ('id', 'status', 'detail', 'revision', 'last_seen')
    }}]
    with store.connect() as c:
        row = c.execute('SELECT body FROM snapshots ORDER BY imported DESC LIMIT 1').fetchone()
        if row:
            evidence.append({'evidenceId': 'latest-snapshot', 'kind': 'monitor', 'content': json.loads(row['body'])})
    previous = [r for r in issue['diagnoses'] if r['body'].get('engine') == 'eve-cpa-1'][:2]
    for entry in previous:
        evidence.append({'evidenceId': 'previous-' + entry['id'][:16], 'kind': 'previous-model-not-fact', 'content': entry['body']})
    for event in issue['events'][:12]:
        evidence.append({'evidenceId': f"event-{event['id']}", 'kind': 'event', 'content': event})
    for outcome in issue['outcomes'][:8]:
        diagnosis = next((r['body'] for r in issue['diagnoses'] if r['id'] == outcome['revision']), {})
        solution = next((s for s in diagnosis.get('solutions', []) if s['id'] == outcome['solution']), None)
        evidence.append({'evidenceId': f"outcome-{outcome['id']}", 'kind': 'human-feedback', 'content': {'result': outcome, 'solution': solution}})
    seen = set()
    for query in [key, key.rsplit('.', 1)[-1]]:
        for hit in store.search(query)[:4]:
            identity = (hit['kind'], hit['id'])
            if identity in seen:
                continue
            seen.add(identity)
            evidence.append({'evidenceId': f'history-{len(seen)}', 'kind': 'historical-not-current', 'content': hit})
    packet = {'issue': key, 'revision': issue['revision'], 'question': question, 'evidence': evidence, 'variant': 'baseline'}
    # Remove whole optional records, never truncate JSON or current evidence.
    while len(encode(packet).encode()) > 70000 and len(evidence) > 2:
        evidence.pop()
    if len(encode(packet).encode()) > 70000:
        raise ValueError('当前证据超过诊断输入容量')
    return packet


def diagnose_remote(packet):
    result = subprocess.run([
        'ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'macmini',
        'cd ~/projects/win-agent-ops-eve/eve-service && node diagnose.mjs'
    ], input=encode(packet), text=True, capture_output=True, timeout=215)
    if result.returncode:
        raise RuntimeError('Eve/CPA 诊断失败；未返回规则结果冒充模型。' + redact(result.stderr)[-500:])
    report = json.loads(result.stdout)
    if report.get('issue') != packet['issue'] or report.get('revision') != packet['revision']:
        raise ValueError('诊断与请求证据版本不匹配')
    return report
