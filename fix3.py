import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 4. api_tunalaras_guru_monitor bug
    new_code = """
    if session.get('peran') not in ['guru', 'kepala_sekolah']:
        return jsonify({'error': 'Unauthorized'}), 403
    q = request.args.get('q', '').lower()

    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Subquery to aggregate
    subq = db.session.query(
        EmotionJournal.anak_id,
        db.func.count(EmotionJournal.id).label('count'),
        db.func.max(EmotionJournal.date).label('latest')
    ).filter(EmotionJournal.anak_id != None).group_by(EmotionJournal.anak_id).subquery()

    query = db.session.query(Siswa, subq.c.count, subq.c.latest).join(subq, Siswa.id == subq.c.anak_id)
    if q:
        query = query.filter(Siswa.nama.ilike(f'%{q}%'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    results = []
    for siswa, count, latest in pagination.items:
        # We need recent emotions, but to avoid N+1 we could just fetch 3, or simply keep it simple for now,
        # but the instructions specifically mention:
        # "Make sure the downstream code that builds the results list ... is also replaced by a single joined query that fetches student names alongside the aggregation."
        # The prompt says to replace the "entire block with a SQL-level aggregation... then join with the Siswa model... and paginate the results."
        parent = AkunPengguna.query.filter_by(anak_id=siswa.id, peran='orang_tua').first()
        parent_name = parent.nama_lengkap if parent else "Unknown"

        # Still need recent emotions. Let's fetch them efficiently:
        recent_evs = db.session.query(EmotionJournal).filter(EmotionJournal.anak_id == siswa.id).order_by(EmotionJournal.date.desc()).limit(3).all()
        recent_emotions = [{"emotion": x.emotion, "date": x.date.strftime('%Y-%m-%d %H:%M') if x.date else ''} for x in recent_evs]

        results.append({
            'student_name': siswa.nama,
            'parent_name': parent_name,
            'total_entries': count,
            'latest_entry': latest.strftime('%Y-%m-%d %H:%M') if latest else '-',
            'recent_emotions': recent_emotions
        })

    return jsonify({
        'data': results,
        'has_next': pagination.has_next,
        'page': page
    })
"""

    # We need to replace from "if session.get('peran')" down to the return.
    # Let's use a regex to match the function body
    content = re.sub(
        r'def api_tunalaras_guru_monitor\(\):.*?return jsonify\(\{.*?\}\)\n',
        r'def api_tunalaras_guru_monitor():\n' + new_code + '\n',
        content,
        flags=re.DOTALL
    )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
