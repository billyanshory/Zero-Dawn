import threading
import time
import requests
import os
import sqlite3

# Set environment variable to force in-memory DB for testing
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'

from app import app, db

def run_app():
    with app.app_context():
        db.create_all()
    app.run(port=5000, use_reloader=False)

run_app()
