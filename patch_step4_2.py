import re

with open('app.py', 'r') as f:
    content = f.read()

handler_old = """@limiter.limit("20 per minute")
def handle_ot_jadwal():
    if request.method == 'POST':
        if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            data = request.json
            db.session.add(OrangTuaJadwal(
                anak_id=session.get('anak_id'),
                schedule_time=data.get('time'),
                medication_name=data.get('medication_name')
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500

    # GET method
    q = OrangTuaJadwal.query
    if session.get('peran') == 'orang_tua':
        q = q.filter_by(anak_id=session.get('anak_id'))
    elif session.get('peran') in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):
        q = q.filter_by(anak_id=request.args.get('anak_id'))

    logs = q.order_by(OrangTuaJadwal.schedule_time.asc()).all()
    res = []
    for l in logs:
        res.append({
            "id": l.id,
            "time": l.schedule_time.strftime("%H:%M") if l.schedule_time else "",
            "medication_name": l.medication_name,
            "notified": l.notified
        })
    return jsonify(res)"""
handler_new = """@limiter.limit("20 per minute")
def handle_ot_jadwal():
    from datetime import datetime as dt_parse, time as dt_time
    if request.method == 'POST':
        if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            data = request.json
            time_str = data.get('time')
            parsed_time = dt_parse.strptime(time_str, '%H:%M').time() if time_str else None
            db.session.add(OrangTuaJadwal(
                anak_id=session.get('anak_id'),
                schedule_time=parsed_time,
                medication_name=data.get('medication_name')
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Terjadi kesalahan saat menyimpan data.'}), 500

    # GET method
    q = OrangTuaJadwal.query
    if session.get('peran') == 'orang_tua':
        q = q.filter_by(anak_id=session.get('anak_id'))
    elif session.get('peran') in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):
        q = q.filter_by(anak_id=request.args.get('anak_id'))

    logs = q.order_by(OrangTuaJadwal.schedule_time.asc()).all()
    res = []
    for l in logs:
        res.append({
            "id": l.id,
            "time": l.schedule_time.strftime("%H:%M") if isinstance(l.schedule_time, dt_time) else str(l.schedule_time) if l.schedule_time else "",
            "medication_name": l.medication_name,
            "notified": l.notified
        })
    return jsonify(res)"""
content = content.replace(handler_old, handler_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching part 2.")
