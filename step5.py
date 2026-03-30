with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Validation PMB Register
pmb_validation = """
        if PendaftaranPMB.query.filter(func.lower(PendaftaranPMB.nama) == func.lower(nama)).first():
            return jsonify({'success': False, 'error': 'Nama pendaftar sudah terdaftar. Jangan lakukan submit ganda.'})
"""
content = content.replace("ijazah_filename = \"\"", pmb_validation + "\n        ijazah_filename = \"\"")

# 2. Validation Tracer Study
tracer_validation = """
        npm_input = request.form.get('npm')
        if TracerStudy.query.filter_by(npm=npm_input).first():
            flash('NPM ini sudah mengisi tracer study.', 'error')
            return redirect(request.referrer or url_for('index'))
"""
content = content.replace("new_tracer = TracerStudy(", tracer_validation + "\n        new_tracer = TracerStudy(")

# 3. Notification Model
notif_model = """
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), index=True)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
"""
content = content.replace("class TracerStudy(db.Model):", notif_model + "\nclass TracerStudy(db.Model):")

# 4. Notification Route
notif_route = """
@app.route('/api/notifications/poll', methods=['GET'])
@login_required
def api_notifications_poll():
    npm = session.get('npm')
    if not npm:
        return jsonify([])
    notifs = Notification.query.filter_by(npm=npm, is_read=False).all()
    res = [{'id': n.id, 'message': n.message} for n in notifs]
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return jsonify(res)
"""
content = content.replace("@app.route('/api/pmb/check', methods=['GET'])", notif_route + "\n@app.route('/api/pmb/check', methods=['GET'])")

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
