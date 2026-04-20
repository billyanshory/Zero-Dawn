with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """@app.before_request
def assign_request_id():
    g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]"""

replace = """@app.before_request
def assign_request_id():
    g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]

@app.before_request
def _refresh_session():
    if session.get('user_id'):
        session.permanent = True
        session.modified = True"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
