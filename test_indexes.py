from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import importlib
import os

os.environ['SQLALCHEMY_DATABASE_URI']='sqlite:///slb.db'
os.environ['SECRET_KEY']='test'
os.environ['REDIS_URL']='redis://localhost:6379/0'

app_module = importlib.import_module("sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort )")
app = app_module.app
db = app_module.db

with app.app_context():
    # Force recreate to apply indexes
    db.create_all()

    import sqlite3
    conn = sqlite3.connect('slb.db')
    c = conn.cursor()
    c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
    indexes = c.fetchall()
    for index in indexes:
        print(index)
    conn.close()
