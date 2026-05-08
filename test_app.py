import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['WTF_CSRF_ENABLED'] = 'False'
from runpy import run_path
run_path('les-latihan-bimbel-13 ( pythonanywhere - SQLite + RawSQL to MySQL + SQLAlchemy ORM - Gemini 3.1 Pro ).py', run_name='__main__')
