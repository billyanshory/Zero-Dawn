import os
import threading
import time

os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-key'

import pymysql

import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

from werkzeug.serving import make_server

app = app_module.app
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

with app.app_context():
    app_module.db.create_all()

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print("Starting server...")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

server = ServerThread(app)
server.start()

try:
    time.sleep(2)
    print("Server booted successfully on port 5000")
finally:
    pass
