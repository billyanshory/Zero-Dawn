with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """@app.route('/orang-tua/api/vapid_public_key')
# INTENTIONALLY PUBLIC: VAPID public keys are inherently public by design.
def vapid_public_key() -> Response | str | tuple[Response, int]:"""

replace = """@app.route('/api/admin/vapid-fingerprint', methods=['GET'])
@require_auth(roles=[ROLE_KEPALA_SEKOLAH])
def get_vapid_fingerprint() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the get_vapid_fingerprint endpoint.\"\"\"
    if not PUSH_NOTIFICATIONS_ENABLED:
        return jsonify({'error': 'Push not enabled'}), 404
    _pub_fp = hashlib.sha256(VAPID_PUBLIC_KEY.encode()).hexdigest()[:16]
    return jsonify({'fingerprint': _pub_fp})

@app.route('/orang-tua/api/vapid_public_key')
# INTENTIONALLY PUBLIC: VAPID public keys are inherently public by design.
def vapid_public_key() -> Response | str | tuple[Response, int]:"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
