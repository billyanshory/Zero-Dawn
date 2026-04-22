sed -i 's|mysql+pymysql://alhijrahdelima_user:4lh1jr4hd3l1m5A!@localhost/alhijrahdelima|sqlite:///:memory:|' app.py
python test_endpoints.py
