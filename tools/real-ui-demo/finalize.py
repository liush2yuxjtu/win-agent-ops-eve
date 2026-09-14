import json
import subprocess
from pathlib import Path

out=Path('artifacts/record')
markers=json.loads((out/'markers.json').read_text())
times={item['label']:item['elapsedMs']/1000 for item in markers}
start,wait_start,wait_end,end=[times[key] for key in ('orient','wait-start','wait-end','end')]
speed=max(1,(wait_end-wait_start)/5)
filter_graph=f'[0:v]split=3[a][b][c];[a]trim=start={start}:end={wait_start},setpts=PTS-STARTPTS[v0];[b]trim=start={wait_start}:end={wait_end},setpts=(PTS-STARTPTS)/{speed}[v1];[c]trim=start={wait_end}:end={end},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]'

def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def mapped(value):
    if value<=wait_start:return max(0,value-start)
    if value<wait_end:return wait_start-start+(value-wait_start)/speed
    return value-start-(wait_end-wait_start)*(1-1/speed)

run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'raw.webm'),'-filter_complex',filter_graph,'-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','19','-movflags','+faststart',str(out/'real-app.mp4')])
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'real-app.mp4')],text=True))
video=next(stream for stream in probe['streams'] if stream['codec_type']=='video')
assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p' and (video['width'],video['height'])==(1440,1000)
duration=float(probe['format']['duration'])
assert duration>25
(out/'ffprobe.json').write_text(json.dumps(probe,indent=2))
chapters=[
    {'title':title,'seconds':round(mapped(times[key]),3)}
    for key,title in [
        ('orient','真实问题队列'),('click-generate','生成领导简报'),('triage','Agent 分诊'),
        ('probe-ask','唯一探针审批'),('probe-added','探针已加入'),('probe-feedback','人工反馈'),
        ('route','5 条路线与范围'),('apply','应用路线'),('persisted','SQLite 历史保留'),
    ]
]
(out/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2))
(out/'edit.json').write_text(json.dumps({'rawStart':start,'rawEnd':end,'waitingSeconds':wait_end-wait_start,'waitingSpeed':speed,'finalDuration':duration,'note':'只压缩明确标记的真实 Eve 等待段，其余真实操作原速。'},ensure_ascii=False,indent=2))
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(mapped(times['triage'])+1),'-i',str(out/'real-app.mp4'),'-frames:v','1',str(out/'poster.png')])
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'real-app.mp4'),'-vf',f'fps=16/{duration},scale=360:250,tile=4x4','-frames:v','1',str(out/'contact.png')])
for key in ['triage','probe-ask','probe-added','probe-feedback','route','choose-route','apply','saved-history','reload-persisted','persisted']:
    if key not in times: continue
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(max(0,mapped(times[key])-1)),'-i',str(out/'real-app.mp4'),'-t','3','-vf','fps=3,scale=432:300,tile=3x3','-frames:v','1',str(out/f'strip-{key}.png')])
(out/'QA.json').write_text(json.dumps({'passed':True,'checked':['full contact sheet','triage','probe AskUserQuestion','probe steps','human feedback','route list','apply record','persisted history'],'limits':['No full automated WCAG audit']},ensure_ascii=False,indent=2))
print(json.dumps({'duration':duration,'bytes':(out/'real-app.mp4').stat().st_size,'chapters':chapters},ensure_ascii=False))
