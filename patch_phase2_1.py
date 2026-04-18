with open("app.py", "r") as f:
    lines = f.readlines()

health_endpoints = """
@app.route('/healthz', methods=['GET'])
@csrf.exempt
def healthz() -> Response:
    \"\"\"Liveness probe for load balancers.\"\"\"
    return jsonify({"status": "alive"}), 200

limiter.exempt(healthz)

@app.route('/readyz', methods=['GET'])
@csrf.exempt
def readyz() -> Response:
    \"\"\"Readiness probe for load balancers.\"\"\"
    db_ok = False
    redis_ok = False
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except Exception as e:
        app.logger.warning("Readiness probe DB check failed", exc_info=True)

    try:
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            redis_ok = True
        else:
            r = redis.from_url(redis_url, socket_timeout=2)
            r.ping()
            redis_ok = True
    except Exception as e:
        app.logger.warning("Readiness probe Redis check failed", exc_info=True)

    if db_ok and redis_ok:
        return jsonify({"status": "ready", "checks": {"db": True, "redis": True}}), 200
    else:
        resp = jsonify({"status": "not_ready", "checks": {"db": db_ok, "redis": redis_ok}})
        resp.status_code = 503
        resp.headers['Retry-After'] = '5'
        return resp

limiter.exempt(readyz)
"""

new_lines = []
for line in lines:
    if line.startswith("def add_security_headers(response: Response) -> Response:"):
        new_lines.append(health_endpoints + "\n")
        new_lines.append(line)
    else:
        new_lines.append(line)

with open("app.py", "w") as f:
    f.writelines(new_lines)
