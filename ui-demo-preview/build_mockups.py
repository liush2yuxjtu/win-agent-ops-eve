import html
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
(ROOT/'scenes').mkdir(parents=True,exist_ok=True)
INK='#202a28'; GREEN='#214f42'; MUTED='#626d68'; LINE='#d5dbd4'; PAPER='#f4f2ed'; WHITE='#fefdf9'
parts=[]
def rect(x,y,w,h,fill=WHITE,stroke=LINE,r=12):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
def text(x,y,s,size=20,color=INK,weight=400):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{html.escape(s)}</text>')
def lines(x,y,rows,size=19,color=INK,gap=30):
    for i,row in enumerate(rows):text(x,y+i*gap,row,size,color)
def button(x,y,w,label,primary=True):
    rect(x,y,w,44,GREEN if primary else WHITE,GREEN,6);text(x+18,y+28,label,17,'#ffffff' if primary else GREEN,600)
def arrow(x,y):
    parts.append(f'<path d="M{x} {y} l0 30 8 -8 8 17 8 -4 -8 -16 12 -1 Z" fill="{INK}" stroke="white" stroke-width="2"/>')
def chrome(index,title,sub):
    parts.clear();rect(0,0,1280,720,PAPER,PAPER,0)
    text(34,44,'W/  业务运行简报',24,GREEN,700);text(845,42,'领导版设计稿 · 演示情景，非真实事故',16,MUTED)
    rect(24,80,215,612,WHITE,LINE,10)
    text(44,119,'需要关注',18,GREEN,650)
    rect(38,145,187,114,'#f7e7e1','#f7e7e1',7);text(51,177,'客户登录异常',20,INK,650)
    text(51,208,'优先处理',17,'#9d382f',600);text(51,236,'业务影响待确认',15,MUTED)
    nav=['业务影响','原因判断','独立方案比较','形成建议','决策留痕']
    for i,name in enumerate(nav):
        y=292+i*53
        if i==index:rect(38,y-24,187,43,'#e8eee7','#e8eee7',5)
        text(53,y+4,name,18,GREEN if i==index else MUTED,650 if i==index else 400)
    text(43,637,'建议不等于执行授权',15,MUTED);text(43,665,'技术细节按需查看',15,MUTED)
    text(273,119,title,31,INK,650);text(275,151,sub,17,MUTED)
def save(name):
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720"><g font-family="PingFang SC, Microsoft YaHei, sans-serif">'+''.join(parts)+'</g></svg>'
    (ROOT/'scenes'/name).write_text(svg)

chrome(0,'先看业务是否受阻','一句话看清问题，不用先读日志。')
rect(272,181,978,120);text(296,219,'客户暂时无法登录，在线下单可能受阻。',27,INK,650)
text(296,253,'本例发生在一次系统升级后；是否影响全部客户，仍需核实。',19,MUTED)
for x,label,big,small in [(272,'业务影响','客户自助服务受阻','订单损失尚未确认'),(604,'处理优先级','建议优先处理','先恢复业务，再追查原因'),(936,'负责人','技术与客服协同','不无依据归责个人')]:
    rect(x,323,314,177);text(x+21,359,label,17,MUTED);text(x+21,404,big,23,INK,600);text(x+21,452,small,17,MUTED)
rect(272,522,978,150,'#e8eee7');text(296,559,'现在需要决定什么？',23,GREEN,650)
text(296,594,'在“恢复系统”和“保障紧急业务”之间，选择一条处理路线。',20)
button(1020,606,204,'查看判断与方案');arrow(1170,631)
save('01-entry.svg')

chrome(1,'发生了什么，为什么这么判断','把事实、推测和未知分开，避免把猜测当结论。')
for y,label,color,rows in [(184,'已经确认',GREEN,['演示情景中，客户登录失败，故障出现在升级之后。','当前不能据此认定升级就是故障原因。']), (344,'倾向判断','#8b5a16',['可能与此次变更有关，建议优先核对变更影响。','现有信息还不足以确认具体原因或责任归属。']), (504,'仍需核实',MUTED,['哪些客户受影响、是否有订单积压，以及上一版本的数据兼容性。','这些信息将影响方案能否执行，不能用“页面能打开”代替业务恢复。'])]:
    rect(272,y,978,144);text(296,y+38,label,22,color,650);lines(296,y+79,rows,20,gap=32)
save('02-context.svg')

plans=[
 ('A','修复当前服务','保留现有功能，修复具体故障','原因仍未确认','恢复时间可能较长'),
 ('B','恢复上一稳定版本','回到已验证的可用状态','需确认数据兼容','近期新功能暂不可用'),
 ('C','切换备用服务','绕开故障，恢复线上服务','需有可用备用服务','同步与切换有风险'),
 ('D','临时改为人工受理','先保障紧急订单继续处理','需安排客服与运营','增加人力，系统仍需修复'),
 ('E','隔离重建后替换','解决复杂环境问题后替换','需独立环境与验收','准备周期通常更长')]
chrome(2,'五种备选路线，选一条合适的','这是彼此独立的选择，不是必须依次完成的五个步骤。')
rect(272,181,978,413)
for x,s in [(294,'可独立选择的方案'),(516,'能解决什么'),(806,'适用前提'),(1002,'主要代价')]:text(x,218,s,17,MUTED,600)
for i,(letter,title,outcome,when,risk) in enumerate(plans):
    y=240+i*68
    if letter=='B':rect(282,y,958,63,'#e8eee7','#e8eee7',5)
    text(295,y+36,letter,20,GREEN,700);text(330,y+36,title,19,INK,600)
    text(516,y+36,outcome,17);text(806,y+36,when,16,MUTED);text(1002,y+36,risk,16,MUTED)
text(291,625,'时间、费用和人力均待责任团队评估，不编造“几分钟恢复”或成功率。',18,MUTED)
button(964,642,274,'优先评估方案 B');arrow(1180,661)
save('03-action.svg')

chrome(3,'建议优先评估：恢复上一稳定版本','本例推荐有前提，不代表现在就可以执行。')
rect(272,183,622,304)
text(298,224,'预期收益',18,MUTED);text(298,264,'尽快回到已验证的业务状态',27,GREEN,650)
lines(298,306,['本例假设上一稳定版本仍可用。','如果数据兼容，恢复旧版本可能比继续定位更快。','如果兼容性不成立，这条路线就不适用。'],20,gap=34)
text(298,446,'独立目标：恢复线上服务，不是定位根因的一个步骤。',17,MUTED)
rect(916,183,334,304,'#e8eee7');text(940,225,'需要领导确认的取舍',23,GREEN,650)
lines(940,273,['接受近期新功能暂时下线','接受评估后的服务切换窗口','明确技术与业务协调人'],19,gap=42)
text(940,439,'授权范围与时间另行确认',17,MUTED)
rect(272,511,978,168);text(298,549,'怎样判断这条方案有效？',22,INK,650)
lines(298,586,['客户能登录并完成下单；客服确认关键业务可继续。','不能只凭技术检查通过，就宣布业务已经恢复。'],19,gap=31)
button(1003,617,220,'形成待审批建议');arrow(1171,640)
save('04-result.svg')

chrome(4,'决定可追溯，执行另有授权','记住为什么这样选，也记住后来有没有用。')
rect(272,182,978,129,'#e8eee7');text(298,225,'已形成建议：恢复上一稳定版本',28,GREEN,650)
text(298,269,'本地演示状态 · 尚未批准执行 · 未修改任何真实系统',19,MUTED)
rect(272,334,978,263)
for y,label,value in [(374,'选择理由','优先恢复客户业务，同时保留本次故障证据。'),(431,'执行前提','数据兼容、切换窗口和协调人仍需确认。'),(488,'处理结果','尚未执行，因此不能标记为“已解决”。'),(545,'历史保留','原始问题、原因判断、备选方案和后续反馈分别留存。')]:
    text(298,y,label,18,MUTED);text(440,y,value,20)
text(292,635,'下次遇到相似问题，可以参考真正有效的历史方案。',20,INK,600)
button(1011,641,216,'查看决策记录',False)
save('05-proof.svg')

scenes=[]
for ident,button_label,title,goal,action,subtitle,svg in [
 ('impact','业务影响','先判断业务影响','领导先看影响与紧急程度，不看代码或错误码。','选择客户登录异常，更新业务影响与建议区域。','先看业务受阻，再决定如何处理','01-entry.svg'),
 ('triage','原因判断','事实与推测分开','避免把相关性当根因，把未知项公开。','展开原因判断，查看已确认、倾向和待核实。','哪些已确认，哪些还不知道','02-context.svg'),
 ('options','独立方案','比较五条独立路线','每条方案都能独立选择，明确收益、前提与代价。','选择一个备选方案；后续建议围绕该方案展示。','备选方案不是执行步骤','03-action.svg'),
 ('recommendation','形成建议','推荐理由与授权取舍','明确推荐为什么成立，以及领导要确认什么。','查看推荐方案B的条件，形成待审批建议。','先明确取舍，再决定是否授权','04-result.svg'),
 ('history','决策留痕','记录建议，不冒充执行','保留方案与理由，处理结果等待真实反馈。','查看建议记录、执行前提和未执行状态。','选择可追溯，执行另有授权','05-proof.svg')]:
    scenes.append(dict(id=ident,button=button_label,title=title,goal=goal,action=action,subtitle=subtitle,duration_seconds=6,svg='scenes/'+svg))
manifest={'title':'业务异常，如何决策','source':'/Users/liushiyuwin/projects/win-agent-ops-eve','session':os.environ.get('PI_SESSION_ID','unavailable via shell'),'stage':'mockup-awaiting-approval','scenes':scenes}
(ROOT/'scenes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
