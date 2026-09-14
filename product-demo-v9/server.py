#!/usr/bin/env python3
"""Serve the standalone Web Mock TUI on loopback only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes

HERE = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def reply(self, status, body, mime='application/json'):
        payload = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/health':
            return self.reply(200, json.dumps({'app': 'win-agent-ops-mock-tui-v9', 'mode': 'web-mock-tui', 'productionActions': False}))
        if path in ('/', '/index.html'):
            return self.reply(200, (HERE / 'index.html').read_bytes(), 'text/html')
        if path == '/app.js':
            return self.reply(200, (HERE / 'app.js').read_bytes(), 'text/javascript')
        if path == '/demo.css':
            return self.reply(200, (HERE / 'demo.css').read_bytes(), 'text/css')
        self.reply(404, json.dumps({'error': 'not found'}))


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8772), Handler)
    print('Web Mock TUI V9 http://127.0.0.1:8772', flush=True)
    server.serve_forever()
