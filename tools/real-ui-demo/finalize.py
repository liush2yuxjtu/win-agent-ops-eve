import json
import subprocess
from pathlib import Path
out=Path('artifacts/record')
markers=json.loads((out/'markers.json').read_text());t={m['label']:m['elapsedMs']/1000 for m in markers}
start,ws,we,end=[t[k] for k in ('orient','wait-start','wait-end','end')];speed=max(1,(we-ws)/5)
f=f'[0:v]split=3[a][b][c];[a]trim=start={start}:end={ws},setpts=PTS-STARTPTS[v0];[b]trim=start={ws}:end={we},setpts=(PTS-STARTPTS)/{speed}[v1];[c]trim=start={we}:end={end},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]'
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'raw.webm'),'-filter_complex',f,'-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','19','-movflags','+faststart',str(out/'real-app.mp4')])
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'real-app.mp4')],text=True));video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p' and (video['width'],video['height'])==(1440,1000)
duration=float(probe['format']['duration']);assert duration>30
(out/'ffprobe.json').write_text(json.dumps(probe,indent=2))
def mapped(time):
 if time<=ws:return max(0,time-start)
 if time<we:return ws-start+(time-ws)/speed
 return time-start-(we-ws)*(1-1/speed)
chapters=[{'title':title,'seconds':round(mapped(t[k]),3)} for k,title in [('orient','真实工作台'),('click-generate','生成领导简报'),('impact','业务影响'),('triage','原因与证据边界'),('plans','独立处理方案'),('review','确认前看取舍'),('reload','刷新验证'),('persisted','SQLite 历史保留')]]
(out/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2));(out/'edit.json').write_text(json.dumps({'rawStart':start,'rawEnd':end,'waitingSeconds':we-ws,'waitingSpeed':speed,'finalDuration':duration,'note':'只加速明确标记的真实模型等待段，其他实际操作原速。'},ensure_ascii=False,indent=2))
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(mapped(t['impact'])+2),'-i',str(out/'real-app.mp4'),'-frames:v','1',str(out/'poster.png')])
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'real-app.mp4'),'-vf',f'fps=16/{duration},scale=360:250,tile=4x4','-frames:v','1',str(out/'contact.png')])
for key in ['click-select-issue','click-generate','wait-end','impact','triage','plans','click-try-alternative','click-return-first','chosen-plan','click-open-confirm','review','click-cancel-confirm','reload','persisted']:
 if key not in t and key in ('click-try-alternative','click-return-first') and json.loads((out/'proof.json').read_text())['solutions']==1:continue
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(max(0,mapped(t[key])-1)),'-i',str(out/'real-app.mp4'),'-t','3','-vf','fps=3,scale=432:300,tile=3x3','-frames:v','1',str(out/f'strip-{key}.png')])
print(json.dumps({'duration':duration,'bytes':(out/'real-app.mp4').stat().st_size,'chapters':chapters},ensure_ascii=False))
