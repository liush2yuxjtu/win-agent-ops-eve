#!/usr/bin/env python3
"""Loopback ops workbench with remote Eve diagnosis and no production mutations."""
import argparse
import http.cookies
import json
import os
import secrets
import sqlite3
import uuid
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from store import Store, ROOT, SOURCE, encode
from model import evidence_packet, diagnose_remote

class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Do not log cookies or query payloads.

    def headers_safe(self):
        return self.headers.get('Host') in self.server.hosts and self.headers.get('Sec-Fetch-Site')!='cross-site'

    def authorized(self):
        cookie=http.cookies.SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except http.cookies.CookieError: return False
        return 'ops_session' in cookie and secrets.compare_digest(cookie['ops_session'].value,self.server.session)

    def reply(self,status,data,mime='application/json',cookie=False):
        payload=encode(data).encode() if mime=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',mime+'; charset=utf-8')
        self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie: self.send_header('Set-Cookie',f'ops_session={self.server.session}; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers(); self.wfile.write(payload)

    def do_GET(self):
        if not self.headers_safe(): return self.reply(403,{'error':'仅接受本机同源请求'})
        path=urlsplit(self.path).path
        assets={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
        if path in assets:
            file,mime=assets[path]
            return self.reply(200,(ROOT/'web'/file).read_bytes(),mime,cookie=path=='/')
        if path=='/health': return self.reply(200,{'app':'win-agent-ops','version':3,'diagnosis':'eve-cpa-1','ui':'leader-live-v1'})
        if not self.authorized(): return self.reply(401,{'error':'请从首页进入'})
        args=parse_qs(urlsplit(self.path).query)
        try:
            with self.server.lock:
                if path=='/api/state':
                    result=self.server.store.state(); result['csrf']=self.server.csrf
                    result['collector']['pollError']=self.server.poll_error
                elif path=='/api/issue': result=self.server.store.issue(args.get('id',[''])[0])
                elif path=='/api/quality': result=self.server.store.quality()
                elif path=='/api/model-run': result=self.server.store.model_run(args.get('id',[''])[0])
                elif path=='/api/search': result={'results':self.server.store.search(args.get('q',[''])[0])}
                else: return self.reply(404,{'error':'接口不存在'})
            self.reply(200,result)
        except KeyError: self.reply(404,{'error':'问题不存在'})
        except Exception: self.reply(500,{'error':'数据读取失败；已保留原数据，请检查服务日志和数据库完整性'})

    def do_POST(self):
        if not self.headers_safe() or self.headers.get('Origin') not in self.server.origins:
            return self.reply(403,{'error':'拒绝跨站写入'})
        if not self.authorized() or not secrets.compare_digest(self.headers.get('X-CSRF-Token',''),self.server.csrf):
            return self.reply(403,{'error':'会话或 CSRF 校验失败；请刷新页面'})
        try:
            if self.headers.get('Content-Type')!='application/json': raise ValueError('需要 JSON')
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=12000: raise ValueError('请求过大或为空')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict): raise ValueError('请求须为对象')
            with self.server.lock:
                if self.path=='/api/refresh':
                    result=self.server.store.refresh(self.server.source)
                    self.server.poll_error=None
                elif self.path=='/api/diagnose':
                    key=body.get('issue')
                    question=body.get('question','解释这个问题，比较根因并给出最多五个互补方案。')
                    if not isinstance(key,str) or not isinstance(question,str) or len(question)>2000: raise ValueError('问题或追问格式无效')
                    packet=evidence_packet(self.server.store,key,question)
                    run_id=str(uuid.uuid4())
                    try: self.server.store.begin_model_run(run_id,packet)
                    except sqlite3.IntegrityError: return self.reply(409,{'error':'该问题已有诊断进行中'})
                    def work():
                        try:
                            report=diagnose_remote(packet)
                            self.server.store.finish_model_run(run_id,report=report)
                        except Exception as exc:
                            self.server.store.finish_model_run(run_id,error=str(exc))
                    threading.Thread(target=work,daemon=True).start()
                    result={'runId':run_id,'state':'running'}
                elif self.path in ('/api/decision','/api/outcome'):
                    result=self.server.store.record(body,self.path.rsplit('/',1)[1])
                else: return self.reply(404,{'error':'接口不存在'})
            self.reply(200,result)
        except (ValueError,KeyError) as exc: self.reply(400,{'error':str(exc)[:200]})
        except Exception: self.reply(500,{'error':'记录失败；未把操作报告为成功'})


def main():
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8766); p.add_argument('--db'); p.add_argument('--source'); args=p.parse_args()
    os.umask(0o077)
    store=Store(args.db) if args.db else Store()
    server=Server(('127.0.0.1',args.port),Handler)
    server.store=store; server.source=SOURCE if not args.source else __import__('pathlib').Path(args.source)
    server.lock=threading.Lock(); server.poll_error=None
    server.session=secrets.token_urlsafe(32); server.csrf=secrets.token_urlsafe(32)
    server.hosts={f'127.0.0.1:{args.port}',f'localhost:{args.port}'}
    server.origins={'http://'+h for h in server.hosts}
    with server.lock: store.refresh(server.source); store.backup()
    def poll():
        cycles=0
        while True:
            time.sleep(30)
            try:
                with server.lock:
                    store.refresh(server.source); cycles+=1
                    if cycles%120==0: store.backup()
                    server.poll_error=None
            except Exception as exc:
                server.poll_error=type(exc).__name__+'：自动导入失败；当前显示最后保存的证据'
                print(server.poll_error,flush=True)
    threading.Thread(target=poll,daemon=True).start()
    print(f'运维工作台 http://127.0.0.1:{args.port}；只读采集，每 30 秒；采纳不执行',flush=True)
    server.serve_forever()

if __name__=='__main__': main()
