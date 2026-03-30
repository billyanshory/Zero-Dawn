#!/bin/bash
export FLASK_APP="kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py"
export SECRET_KEY="test_key_123"
export DATABASE_URL="sqlite:///test.db"
# Set up a test DB just to be safe
sed -i "s/app.config\['SQLALCHEMY_DATABASE_URI'\] = 'mysql+pymysql.*/app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:\/\/\/test.db')/" "kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py"
sed -i "s/app.config\['SQLALCHEMY_ENGINE_OPTIONS'\].*//" "kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py"

python "kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py" > server_pw.log 2>&1 &
PID=$!
sleep 5
python /home/jules/verification/verify_tracer.py
kill $PID
