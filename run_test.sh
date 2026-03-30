#!/bin/bash
export FLASK_APP="kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py"
export SECRET_KEY="test_key_123"
export DB_PASSWORD=""
# Start db if not running
service mariadb start > /dev/null 2>&1 || service mysql start > /dev/null 2>&1 || true
# Create db if not exists
mysql -u root -e "CREATE DATABASE IF NOT EXISTS db_slb;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'tahkilfc_user'@'localhost' IDENTIFIED BY '';" || true
mysql -u root -e "GRANT ALL PRIVILEGES ON db_slb.* TO 'tahkilfc_user'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"
python "kampus-stie-samarinda-17 ( idcloudhost - bug fatal - focus di tracer study ).py" > server.log 2>&1 &
PID=$!
sleep 5
python test_app.py
kill $PID
