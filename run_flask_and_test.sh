python test_endpoints.py &
FLASK_PID=$!
sleep 5 # wait for flask to come up

python /home/jules/verification/verify_idul_adha.py

kill $FLASK_PID
