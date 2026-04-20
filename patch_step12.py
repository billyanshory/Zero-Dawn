with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
@require_auth(roles=STAFF_ROLES)
def generate_iep() -> Response | str | tuple[Response, int]:"""

replace = """@app.route('/guru/iep', methods=['POST'])
@limiter.limit("15 per day", key_func=lambda: str(session.get('user_id') or get_remote_address()))
@require_auth(roles=STAFF_ROLES)
def generate_iep() -> Response | str | tuple[Response, int]:"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
