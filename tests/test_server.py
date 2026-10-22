import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('tracker', Path(__file__).resolve().parents[1] / 'server.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class TrackerTest(unittest.TestCase):
    def test_import_edit_persist_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.DB = Path(tmp) / 'test.sqlite3'
            app.initialize()
            server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            def get():
                with urllib.request.urlopen(base + '/api/jobs') as response:
                    return json.load(response)
            def post(data):
                request = urllib.request.Request(base + '/api/jobs', json.dumps(data).encode(), {'Content-Type':'application/json'})
                with urllib.request.urlopen(request) as response:
                    return json.load(response)
            try:
                initial = get()
                self.assertEqual(len(initial), 27)
                with urllib.request.urlopen(base) as response:
                    self.assertIn('计算任务', response.read().decode())
                added = post(dict(project='测试', task='训练', status='Running', directory='/test'))
                self.assertEqual(len(get()), 28)
                added.update(status='Finished', result='MAE=0.04 eV', next_action='Check')
                post(added)
                app.initialize()
                saved = next(j for j in get() if j['id']==added['id'])
                self.assertEqual(saved['result'], 'MAE=0.04 eV')
                self.assertEqual(saved['status'], 'Finished')
                self.assertEqual(len(get()), 28)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    post(dict(project='测试', task='', status='Running'))
                self.assertEqual(error.exception.code, 400)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
