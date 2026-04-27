from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://alhijrahdelima_user:4lh1jr4hd3l1m5A!@localhost/alhijrahdelima'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    # Print existing tables
    inspector = db.inspect(db.engine)
    print("Tables:", inspector.get_table_names())
