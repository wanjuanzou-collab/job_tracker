"""Run with python server.py. Data stays in data/jobs.sqlite3."""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data/jobs.sqlite3'
FIELDS = 'submitted project task cluster directory job_id status next_action finished result notes'.split()

def connect():
    return sqlite3.connect(DB)

def initialize():
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY)')
        if not db.execute("SELECT 1 FROM meta WHERE key='initialized'").fetchone():
            for job in json.loads((ROOT / 'data/initial.json').read_text()):
                db.execute('INSERT INTO jobs(payload) VALUES (?)', (json.dumps(job),))
            db.execute("INSERT INTO meta VALUES ('initialized')")

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, content_type='application/json; charset=utf-8'):
        raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/':
            return self.reply(200, (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if self.path == '/api/jobs':
            with connect() as db:
                jobs = [dict(json.loads(p), id=i) for i, p in db.execute('SELECT id,payload FROM jobs ORDER BY id DESC')]
            return self.reply(200, jobs)
        self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/api/jobs':
            return self.reply(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 100000:
                raise ValueError('请求大小不正确')
            data = json.loads(self.rfile.read(length))
            job = {k: str(data.get(k, '')).strip() for k in FIELDS}
            if not job['task'] or not job['project']:
                raise ValueError('请填写项目和计算内容')
            if job['status'] not in ['Submitted', 'Running', 'Finished', 'Failed', 'Cancelled']:
                raise ValueError('状态不正确')
            job_id = data.get('id')
            with connect() as db:
                if job_id is None:
                    job_id = db.execute('INSERT INTO jobs(payload) VALUES (?)', (json.dumps(job),)).lastrowid
                else:
                    if not isinstance(job_id, int):
                        raise ValueError('任务编号不正确')
                    if not db.execute('UPDATE jobs SET payload=? WHERE id=?', (json.dumps(job), job_id)).rowcount:
                        return self.reply(404, {'error': '任务不存在'})
            self.reply(200, dict(job, id=job_id))
        except (ValueError, TypeError, AttributeError) as error:
            self.reply(400, {'error': str(error)})

if __name__ == '__main__':
    initialize()
    ThreadingHTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000'))), Handler).serve_forever()
