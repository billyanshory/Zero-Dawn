python run_flask_bg.py > flask.log 2>&1 &
FLASK_PID=$!
sleep 5
python test_endpoints.py
kill $FLASK_PID
