import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    try:
        data = request.json
        log = TantrumLog(
            student=data.get('student'),
            trigger=data.get('trigger'),
            start_time=str(data.get('start')),
            duration_ms=int(data.get('duration', 0)),
            action=data.get('action')
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500"""

replacement = """    try:
        data = request.json
        student_val = validate_str(data.get('student'), 255)
        trigger_val = validate_str(data.get('trigger'), 255)

        if not student_val or not trigger_val:
            return jsonify({'error': 'Student and trigger are required'}), 400

        log = TantrumLog(
            student=student_val,
            trigger=trigger_val,
            start_time=None,
            duration_ms=int(data.get('duration', 0)) if str(data.get('duration', '0')).isdigit() else 0,
            action=validate_str(data.get('action'), 255)
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        app.logger.error('Failed to save tantrum', exc_info=True)
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
