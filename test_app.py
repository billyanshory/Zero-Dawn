from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import importlib
import os

os.environ['SQLALCHEMY_DATABASE_URI']='sqlite:///slb.db'
os.environ['SECRET_KEY']='test'
os.environ.pop('REDIS_URL', None)

try:
    app_module = importlib.import_module("sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort )")
    app = app_module.app
    with app.test_client() as client:
        res = client.get('/')
        print(f"Status Code: {res.status_code}")
except Exception as e:
    print(f"Error: {e}")
