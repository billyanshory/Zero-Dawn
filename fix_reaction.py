import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    data = request.json
    sec = data.get('time_sec')
    if sec is None and data.get('time_ms') is not None:
        sec = data.get('time_ms') / 1000.0
    log = ReactionTimeLog(time_sec=sec)
    db.session.add(log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({"status": "success"})"""

replacement = """    data = request.json
    try:
        sec = data.get('time_sec')
        if sec is None and data.get('time_ms') is not None:
            sec = float(data.get('time_ms')) / 1000.0
        log = ReactionTimeLog(time_sec=sec)
        db.session.add(log)
        db.session.commit()
    except (TypeError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid time value'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({"status": "success"})"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
