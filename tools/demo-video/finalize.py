import json
import subprocess
from pathlib import Path

out=Path('artifacts/record')
markers=json.loads((out/'markers.json').read_text())
times={m['label']:m['elapsedMs']/1000 for m in markers}
start,ws,we,end=[times[k] for k in ('orient','wait-start','wait-end','end')]
speed=max(1,(we-ws)/5)
filters=f'[0:v]split=3[a][b][c];[a]trim=start={start}:end={ws},setpts=PTS-STARTPTS[v0];[b]trim=start={ws}:end={we},setpts=(PTS-STARTPTS)/{speed}[v1];[c]trim=start={we}:end={end},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]'
def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'raw.webm'),'-filter_complex',filters,'-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','20','-movflags','+faststart',str(out/'demo.mp4')])
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'demo.mp4')],text=True))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
assert (video['width'],video['height'])==(1440,900)
duration=float(probe['format']['duration']);assert duration>30
(out/'ffprobe.json').write_text(json.dumps(probe,indent=2))
def mapped(t):
    if t<=ws:return max(0,t-start)
    if t<we:return ws-start+(t-ws)/speed
    return t-start-(we-ws)*(1-1/speed)
chapters=[{'title':title,'seconds':round(mapped(times[label]),3)} for label,title in [('orient','问题队列'),('question','向 Eve 追问'),('result','中文分诊'),('solutions','互补路径'),('adopted','已采纳 · 未执行'),('reload','重新加载'),('history','这个问题的历史')]]
(out/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2))
(out/'edit.json').write_text(json.dumps({'rawStart':start,'rawEnd':end,'waitingStart':ws,'waitingEnd':we,'waitingSpeed':speed,'finalDuration':duration,'note':'只加速字幕明确标记的真实模型等待段，其他操作原速。'},ensure_ascii=False,indent=2))
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(mapped(times['solutions'])+2),'-i',str(out/'demo.mp4'),'-frames:v','1',str(out/'poster.png')])
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'demo.mp4'),'-vf',f'fps=16/{duration},scale=360:225,tile=4x4','-frames:v','1',str(out/'contact.png')])
for label in ['click-choose-issue','question','click-request-eve','wait-end','result','solutions','click-expand-solution','click-adopt','reload','persisted','history']:
    position=max(0,mapped(times[label])-1)
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(position),'-i',str(out/'demo.mp4'),'-t','3','-vf','fps=3,scale=480:300,tile=3x3','-frames:v','1',str(out/f'strip-{label}.png')])
print(json.dumps({'duration':duration,'size':(out/'demo.mp4').stat().st_size,'chapters':chapters},ensure_ascii=False))
