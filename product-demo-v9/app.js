const issues = [
  {id:'jdaro.auth', priority:'P1', title:'登录异常影响两个相关工作台', description:'监控记录显示两个相关客户工作台都出现登录失败信号，但当前状态尚未重新实测。', detail:'login-401'},
  {id:'scaro.auth', priority:'P1', title:'认证检查失败或尚未完成', description:'未证明用户能够登录；首页和接口正常不代表业务登录可用。', detail:'login-401'},
  {id:'host.clean', priority:'P2', title:'工作目录存在未提交修改', description:'运行源码可能偏离记录版本，需要先区分合法修改、生成文件和未知差异。', detail:'dirty'},
  {id:'jdaro.loaded-version', priority:'P2', title:'运行版本缺少可核验证据', description:'缺少实际加载版本收据，不能只凭磁盘版本判断运行实例。', detail:'startup-receipt-missing'},
  {id:'scaro.clean', priority:'P2', title:'工作目录存在未提交修改', description:'工作区有未提交变化，是否影响服务需要逐项核对。', detail:'dirty'},
  {id:'scaro.loaded-version', priority:'P2', title:'运行版本缺少可核验证据', description:'启动收据缺失，当前运行版本仍需证据确认。', detail:'startup-receipt-missing'},
];
const routes = [
  {title:'先做一次新鲜复现', probe:'用受控测试范围，绕开旧缓存，记录一次真实结果。', solve:'先确认问题现在是否还存在，再决定是否需要变更。', blast:'只读检查面', verify:'得到带实际执行时间的成功或失败证据。', rollback:'只撤掉探针，不改业务配置。', source:'Eve / diagnostic'},
  {title:'核对认证材料状态', probe:'比对认证材料版本、有效期和服务读取结果，不显示秘密值。', solve:'由凭据负责人确认材料状态，再选择轮换或重载。', blast:'认证链与依赖服务', verify:'材料与目标服务匹配，登录验证恢复。', rollback:'保留旧材料和恢复窗口，变更前批准。', source:'Eve / root-cause'},
  {title:'核对运行实例版本', probe:'记录 PID、工作目录、启动时间和实际加载版本收据。', solve:'若发现运行实例落后，再按发布流程重建，不直接清理目录。', blast:'单个运行实例', verify:'运行实例、构建产物和发布记录能够对应。', rollback:'保留原版本和启动收据，按批准流程退出。', source:'Eve / diagnostic'},
  {title:'做一次缓存旁路检查', probe:'对单次受控请求标记不使用旧缓存，并保留请求时间和结果。', solve:'若只有缓存异常，修正缓存生命周期；若仍失败，回到认证链调查。', blast:'单一业务路径', verify:'旁路结果与正常路径差异清楚，负责人确认影响。', rollback:'停止旁路请求，恢复原缓存路径。', source:'Eve / mitigation'},
  {title:'先启用人工业务保障', probe:'探测登录失败对一个受控业务流程的真实影响，不扩大流量。', solve:'根因未明时，人工受理关键业务，给维护团队留出安全窗口。', blast:'关键业务入口', verify:'关键业务有受理记录，恢复后完成回补验收。', rollback:'系统恢复后关闭人工保障，保留回补记录。', source:'Eve / mitigation'},
];
const agentSteps = [
  {title:'读取当前问题', detail:'锁定标题、优先级和证据边界。'},
  {title:'自动添加探针', detail:'把最小复现探针加入处理流程，不改业务。'},
  {title:'寻找复现', detail:'等待一次受控结果，保留成功或失败证据。'},
  {title:'等待人工反馈', detail:'人报告复现、解决或补充说明。'},
];
const state = {
  issueIndex: 0,
  rawOpen: false,
  fixPhase: 'idle',
  agentStep: -1,
  routeIndex: 0,
  feedbackKind: '',
  feedbackText: '',
  applied: false,
  status: 'Agent 已把保存证据整理成问题队列。',
};
const timers = [];
let askTrigger = null;
const $ = selector => document.querySelector(selector);
const make = (tag, className, value) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
};
const selectedIssue = () => issues[state.issueIndex];
const selectedRoute = () => routes[state.routeIndex];
const clearTimers = () => { while (timers.length) window.clearTimeout(timers.pop()); };
const priorityName = priority => ({P0:'立即处理',P1:'高优先',P2:'计划处理',P3:'观察'}[priority] || '观察');
const setStatus = value => { state.status = value; render(); };
const rawText = () => JSON.stringify({
  source: 'legacy-monitor',
  issue: selectedIssue().id,
  status: 'fail',
  detail: selectedIssue().detail,
  snapshotHeartbeat: 'saved-monitor-record',
  note: 'mock TUI；保存记录不是新鲜实测。',
}, null, 2);

function chooseIssue(index) {
  state.issueIndex = (index + issues.length) % issues.length;
  state.routeIndex = 0;
  state.fixPhase = 'idle';
  state.agentStep = -1;
  state.feedbackKind = '';
  state.feedbackText = '';
  state.applied = false;
  clearTimers();
  setStatus('已切换问题：' + selectedIssue().id + '。其他问题仍在队列。');
}

function openAskQuestion() {
  const dialog = $('#ask-question');
  if (!dialog || dialog.open) return;
  askTrigger = document.activeElement;
  $('#ask-issue').textContent = selectedIssue().title;
  $('#ask-description').textContent = '批准后，Agent 自动添加一次最小复现探针，展示处理步骤并等待人工反馈。不会直接修复业务。';
  dialog.showModal();
  window.requestAnimationFrame(() => $('#ask-approve')?.focus());
}

function startFix() {
  clearTimers();
  state.fixPhase = 'running';
  state.agentStep = 0;
  state.feedbackKind = '';
  state.feedbackText = '';
  const messages = [
    'Agent 已接手当前问题，正在读取分诊证据。',
    '探针已自动加入修复流程。没有执行业务修复。',
    'Agent 正在寻找复现候选。结果会交给人确认。',
    '探针流程完成。现在等待人工反馈。',
  ];
  state.status = messages[0];
  render();
  messages.slice(1).forEach((message, index) => {
    timers.push(window.setTimeout(() => {
      state.agentStep = index + 1;
      state.status = message;
      if (index === messages.length - 2) state.fixPhase = 'feedback';
      render();
    }, (index + 1) * 650));
  });
}

function feedback(kind, value = '') {
  state.feedbackKind = kind;
  state.feedbackText = value;
  state.status = '反馈已记录：' + (kind === 'reproduced' ? '问题已复现' : kind === 'solved' ? '问题已解决' : '自定义文字') + '。Agent 可用它更新下一轮分诊。';
  render();
}

function typedFeedback() {
  state.feedbackKind = 'typed';
  render();
  const input = $('#typed-feedback');
  input?.focus();
}

function applyFix() {
  state.applied = true;
  state.status = 'Mock TUI：人已选择并应用这条路线。没有执行生产修复。';
  render();
}

function renderFlowHead(parent) {
  const issue = selectedIssue();
  const head = make('div', 'screen-head');
  const left = make('div');
  left.append(make('span', 'screen-kicker', 'TRIAGE FUNNEL / MOCK TUI'));
  left.append(make('h2', null, issue.title));
  left.append(make('p', null, issue.description));
  head.append(left, make('span', 'priority-chip', issue.priority + ' / ' + priorityName(issue.priority)));
  parent.appendChild(head);
}

function renderSource() {
  const pane = $('#source-pane');
  pane.replaceChildren();
  pane.append(make('p', 'pane-label', 'SOURCE / RAW LOG'));
  pane.append(make('p', 'pane-note', '长文本交给 Agent。人只看整理后的问题。'));
  const details = make('details', 'raw-log');
  details.open = state.rawOpen;
  details.addEventListener('toggle', () => { state.rawOpen = details.open; });
  details.append(make('summary', null, '原始日志（长文本）'));
  details.append(make('pre', null, rawText()));
  pane.appendChild(details);
  const head = make('div', 'queue-head');
  head.append(make('strong', null, 'AGENT EXTRACTED / ' + issues.length + ' ISSUES'), make('span', null, 'title + description'));
  pane.appendChild(head);
  const list = make('div', 'issue-list');
  issues.forEach((issue, index) => {
    const button = make('button', 'issue-item' + (index === state.issueIndex ? ' active' : ''));
    button.dataset.issueId = issue.id;
    button.append(make('span', 'issue-pin'));
    const copy = make('span');
    copy.append(make('strong', null, issue.title), make('small', null, issue.id + ' · ' + issue.priority));
    button.appendChild(copy);
    button.addEventListener('click', () => chooseIssue(index));
    list.appendChild(button);
  });
  pane.appendChild(list);
  pane.append(make('p', 'source-footer', '[read-only evidence]\n[one AskUserQuestion gate]\n[fix: human choice]'));
}

function renderTriage(parent) {
  const section = make('section', 'stage-block');
  section.id = 'triage';
  section.append(make('h3', null, '1. Agent 分诊'));
  section.lastChild.append(make('span', null, 'ALL ISSUES / P0-P3'));
  section.append(make('p', null, 'Agent 把长日志变成标题、描述和优先级。人只挑一个继续。'));
  const grid = make('div', 'triage-grid');
  ['P0', 'P1', 'P2', 'P3'].forEach(priority => {
    const lane = make('div', 'lane ' + priority.toLowerCase());
    const laneHead = make('div', 'lane-head');
    laneHead.append(make('strong', null, priority), make('small', null, priorityName(priority)));
    lane.appendChild(laneHead);
    const itemBox = make('div', 'lane-items');
    const items = issues.filter(issue => issue.priority === priority);
    if (!items.length) itemBox.append(make('div', 'empty', '暂无问题'));
    items.forEach(issue => {
      const index = issues.indexOf(issue);
      const button = make('button', 'triage-card' + (index === state.issueIndex ? ' active' : ''));
      button.append(make('strong', null, issue.title), make('small', null, issue.description));
      button.addEventListener('click', () => chooseIssue(index));
      itemBox.appendChild(button);
    });
    lane.appendChild(itemBox);
    grid.appendChild(lane);
  });
  section.appendChild(grid);
  const selected = make('div', 'selected-line');
  selected.append(make('i'));
  const selectedText = make('div');
  selectedText.append(make('strong', null, '当前选择：' + selectedIssue().title), make('span', null, selectedIssue().description));
  selected.append(selectedText, make('code', null, selectedIssue().id + ' · ' + selectedIssue().detail));
  section.appendChild(selected);
  parent.appendChild(section);
}

function renderAgentSteps(parent) {
  const steps = make('div', 'agent-steps');
  agentSteps.forEach((step, index) => {
    const row = make('div', 'agent-step ' + (state.agentStep > index ? 'done' : state.agentStep === index ? 'active' : 'pending'));
    row.append(make('span', 'step-dot', state.agentStep > index ? '✓' : String(index + 1)));
    const copy = make('div');
    copy.append(make('strong', null, step.title), make('small', null, step.detail));
    row.appendChild(copy);
    steps.appendChild(row);
  });
  parent.appendChild(steps);
}

function renderProbe(parent) {
  const section = make('section', 'stage-block');
  section.id = 'probe';
  section.append(make('h3', null, '2. Probe · ONE APPROVAL GATE'));
  section.lastChild.append(make('span', null, 'ASK USER QUESTION'));
  section.append(make('p', null, '只在添加探针前问一次。批准后自动开始处理和寻找复现。'));
  const card = make('div', 'probe-card');
  const title = state.fixPhase === 'idle' ? '等待一次批准' : state.fixPhase === 'running' ? 'Agent 正在处理…' : '等待人工反馈';
  const copy = state.fixPhase === 'idle' ? '点击 ADD PROBE，弹出 AskUserQuestion。没有其他审批。' : state.fixPhase === 'running' ? 'Agent 自动添加探针，逐步寻找复现；不会直接修复业务。' : '探针已完成本地 Mock 流程。现在由人报告复现、解决或补充说明。';
  card.append(make('h3', null, title), make('p', null, copy));
  if (state.fixPhase !== 'idle') renderAgentSteps(card);
  if (state.fixPhase !== 'idle') card.append(make('pre', 'probe-code', 'probe({\n  issue: "' + selectedIssue().id + '",\n  freshResult: true,\n  record: ["executedAt", "listenerCwd", "loadedVersion"],\n  maxAttempts: 1\n})'));
  const actions = make('div', 'action-row');
  if (state.fixPhase === 'idle') {
    const add = make('button', 'action primary', 'p  ADD PROBE');
    add.addEventListener('click', openAskQuestion);
    actions.appendChild(add);
  }
  card.appendChild(actions);
  if (state.fixPhase === 'feedback') {
    const feedbackBox = make('div', 'feedback-box');
    feedbackBox.append(make('h4', null, 'HUMAN FEEDBACK'), make('p', null, '反馈回到下一轮分诊，不自动关闭问题。'));
    const buttons = make('div', 'action-row');
    const reproduced = make('button', 'action ok', 'r  ISSUE REPRODUCED');
    reproduced.addEventListener('click', () => feedback('reproduced'));
    const solved = make('button', 'action ok', 's  ISSUE SOLVED');
    solved.addEventListener('click', () => feedback('solved'));
    const typed = make('button', 'action', 't  TYPE PROMPT');
    typed.addEventListener('click', typedFeedback);
    buttons.append(reproduced, solved, typed);
    feedbackBox.appendChild(buttons);
    if (state.feedbackKind === 'typed') {
      const input = make('textarea', 'feedback-input');
      input.id = 'typed-feedback';
      input.placeholder = '告诉 Agent 下一轮要注意什么';
      input.value = state.feedbackText;
      input.addEventListener('input', () => { state.feedbackText = input.value; });
      input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (input.value.trim()) feedback('typed', input.value.trim()); } });
      feedbackBox.appendChild(input);
      const save = make('button', 'action primary', '保存文字反馈');
      save.addEventListener('click', () => { if (input.value.trim()) feedback('typed', input.value.trim()); });
      feedbackBox.appendChild(save);
    }
    if (state.feedbackKind === 'reproduced') feedbackBox.append(make('p', 'fix-note', '反馈已记录：问题已复现。'));
    if (state.feedbackKind === 'solved') feedbackBox.append(make('p', 'fix-note', '反馈已记录：问题已解决。'));
    if (state.feedbackKind === 'typed' && state.feedbackText) feedbackBox.append(make('p', 'fix-note', '反馈已记录：自定义文字。'));
    card.appendChild(feedbackBox);
  }
  section.appendChild(card);
  parent.appendChild(section);
}

function renderRoutes(parent) {
  const section = make('section', 'stage-block');
  section.id = 'routes';
  section.append(make('h3', null, '3. Route & Apply Fix'));
  section.lastChild.append(make('span', null, 'HUMAN CHOICE'));
  section.append(make('p', null, 'Agent 给 5 条路线和 Blast Radius。人选中后直接应用 Mock fix。没有第二个审批弹窗。'));
  const list = make('div', 'routes');
  routes.forEach((route, index) => {
    const row = make('div', 'route' + (index === state.routeIndex ? ' selected' : ''));
    const head = make('button', 'route-head');
    head.append(make('span', 'route-rank', '0' + (index + 1)), make('span', 'route-main'), make('span', 'route-source'), make('span', 'route-mark', index === state.routeIndex ? '−' : '+'));
    head.children[1].append(make('strong', null, route.title), make('small', null, route.solve));
    head.children[2].append(make('b', null, 'BLAST RADIUS'), make('span', null, route.blast + ' · ' + route.source));
    head.addEventListener('click', () => { state.routeIndex = index; state.applied = false; render(); });
    row.appendChild(head);
    if (index === state.routeIndex) {
      const detail = make('div', 'route-detail');
      [['复现探针', route.probe], ['解决动作', route.solve], ['影响范围', route.blast], ['验收', route.verify], ['回退', route.rollback], ['适用边界', '需要人工确认适用条件，不能把 Mock 路线当成已修复事实。']].forEach(([label, value]) => {
        const cell = make('div', label === '适用边界' ? 'full' : '');
        cell.append(make('span', null, label), make('p', null, value));
        detail.appendChild(cell);
      });
      const apply = make('button', 'action ' + (state.applied ? 'ok' : 'primary'), state.applied ? '✓ FIX APPLIED · MOCK' : 'a  APPLY SELECTED FIX');
      apply.addEventListener('click', applyFix);
      detail.appendChild(apply);
      row.appendChild(detail);
    }
    list.appendChild(row);
  });
  section.appendChild(list);
  parent.appendChild(section);
}

function renderMain() {
  const pane = $('#main-pane');
  pane.replaceChildren();
  const screen = make('div', 'screen');
  renderFlowHead(screen);
  renderTriage(screen);
  renderProbe(screen);
  renderRoutes(screen);
  pane.appendChild(screen);
}

function renderTrace() {
  const pane = $('#trace-pane');
  pane.replaceChildren();
  const title = make('div', 'trace-title');
  title.append(make('strong', null, 'AGENT TRACE'), make('span', null, state.fixPhase === 'running' ? 'LIVE' : 'READY'));
  pane.appendChild(title);
  const command = make('div', 'trace-block');
  command.append(make('label', null, 'CURRENT COMMAND'), make('div', 'trace-command', 'triage-funnel --issue ' + selectedIssue().id + ' --flow triage > probe > route/apply'));
  pane.appendChild(command);
  const status = make('div', 'trace-block');
  const statusText = state.fixPhase === 'idle' ? 'waiting for one AskUserQuestion gate' : state.fixPhase === 'running' ? 'step ' + (state.agentStep + 1) + ' / 4' : 'waiting for human feedback';
  status.append(make('label', null, 'AGENT STATUS'), make('div', 'trace-status', statusText));
  pane.appendChild(status);
  if (state.fixPhase !== 'idle') {
    const traceSteps = make('div', 'trace-block');
    traceSteps.append(make('label', null, 'STEPS'));
    renderAgentSteps(traceSteps);
    pane.appendChild(traceSteps);
  }
  const keys = make('div', 'trace-block');
  keys.appendChild(make('label', null, 'KEYBOARD'));
  const keyList = make('div', 'key-list');
  [['j / k', 'issue'], ['[ / ]', 'route'], ['l', 'raw log'], ['p', 'AskUserQuestion'], ['r / s / t', 'human feedback'], ['a', 'apply fix']].forEach(([key, label]) => {
    const row = make('div', 'key-row');
    row.append(make('kbd', null, key), make('span', null, label));
    keyList.appendChild(row);
  });
  keys.appendChild(keyList);
  pane.appendChild(keys);
}

function renderStatus() {
  $('#terminal-status').querySelector('.status-text').textContent = state.status;
}
function render() {
  renderSource();
  renderMain();
  renderTrace();
  renderStatus();
}

const askDialog = $('#ask-question');
$('#ask-cancel').addEventListener('click', () => askDialog.close('cancel'));
$('#ask-cancel-icon').addEventListener('click', () => askDialog.close('cancel'));
$('#ask-approve').addEventListener('click', () => askDialog.close('approved'));
askDialog.addEventListener('close', () => {
  const approved = askDialog.returnValue === 'approved';
  if (approved) startFix();
  else {
    state.status = '已取消添加探针。唯一审批门未通过。';
    render();
  }
  askTrigger?.focus?.();
});

document.addEventListener('keydown', event => {
  if (['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
    if (event.key === 'Escape') event.target.blur();
    return;
  }
  if (event.key === 'j' || event.key === 'ArrowDown') { chooseIssue(state.issueIndex + 1); return; }
  if (event.key === 'k' || event.key === 'ArrowUp') { chooseIssue(state.issueIndex - 1); return; }
  if (event.key === '[') { state.routeIndex = (state.routeIndex - 1 + routes.length) % routes.length; state.applied = false; render(); return; }
  if (event.key === ']') { state.routeIndex = (state.routeIndex + 1) % routes.length; state.applied = false; render(); return; }
  if (event.key === 'l') { state.rawOpen = !state.rawOpen; state.status = state.rawOpen ? '原始日志已展开。' : '原始日志已收起。'; render(); return; }
  if (event.key === 'p' && state.fixPhase === 'idle') { openAskQuestion(); return; }
  if (event.key === 'r' && state.fixPhase === 'feedback') { feedback('reproduced'); return; }
  if (event.key === 's' && state.fixPhase === 'feedback') { feedback('solved'); return; }
  if (event.key === 't' && state.fixPhase === 'feedback') { typedFeedback(); return; }
  if (event.key === 'a') { applyFix(); }
});

render();
