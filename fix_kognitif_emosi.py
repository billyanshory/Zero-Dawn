import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    data = request.json
    log = KognitifEmosiLog(
        score=data.get('score'),
        duration_sec=data.get('duration_sec'),
        history=data.get('history')
    )
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
        score_val = int(data.get('score', 0))
        dur_val = float(data.get('duration_sec', 0))
        history_val = validate_str(data.get('history'), 5000)
        log = KognitifEmosiLog(
            score=score_val,
            duration_sec=dur_val,
            history=history_val
        )
        db.session.add(log)
        db.session.commit()
    except (TypeError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid data format'}), 400
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
