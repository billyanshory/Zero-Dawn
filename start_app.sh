export PORT=5001
export SECRET_KEY=test
export SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
gunicorn -k eventlet -w 1 --worker-connections 100 --bind 0.0.0.0:${PORT} --graceful-timeout 5 --timeout 30 --access-logfile - --error-logfile - "masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ):app" &
