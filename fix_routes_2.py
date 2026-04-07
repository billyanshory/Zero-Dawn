import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r'@app\.route\(\'/therapy/log\', methods=\[\'POST\'\]\).*?def index\(\):',
r'''@app.route('/therapy/log', methods=['POST'])
def therapy_log():
    try:
        anak_id = session.get('anak_id') if session.get('peran') == 'orang_tua' else None
        log = EpilepsiLog(
            date=request.form['date'],
            time=request.form['time'],
            trigger=request.form['trigger'],
            notes=request.form['notes'],
            anak_id=anak_id
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging therapy: {e}")
    return redirect(url_for('index', open='modal-terapi-log'))

@app.route('/api/jurnal-kambuh/guru-view')
def api_jurnal_kambuh_guru_view():
    if session.get('peran') not in ['guru', 'kepala_sekolah']:
        return jsonify({'error': 'Unauthorized'}), 403
    page = request.args.get('page', 1, type=int)

    logs = db.session.query(EpilepsiLog, Siswa.nama).join(Siswa, EpilepsiLog.anak_id == Siswa.id).filter(EpilepsiLog.anak_id != None).order_by(EpilepsiLog.created_at.desc()).paginate(page=page, per_page=10, error_out=False)

    results = []
    for log, siswa_nama in logs.items:
        results.append({
            "siswa_nama": siswa_nama,
            "date": log.date,
            "time": log.time,
            "trigger": log.trigger,
            "notes": log.notes
        })
    return jsonify({
        "items": results,
        "has_next": logs.has_next,
        "page": page
    })

@app.route('/')
def index():''', content, flags=re.DOTALL)

content = re.sub(r'def index\(\):\s*try:\s*epilepsi_logs = EpilepsiLog\.query\.order_by\(EpilepsiLog\.created_at\.desc\(\)\)\.limit\(5\)\.all\(\)\s*except:\s*epilepsi_logs = \[\]',
r'''def index():
    try:
        if session.get('peran') == 'orang_tua' and session.get('anak_id'):
            epilepsi_logs = EpilepsiLog.query.filter_by(anak_id=session.get('anak_id')).order_by(EpilepsiLog.created_at.desc()).limit(10).all()
        else:
            epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.created_at.desc()).limit(5).all()
    except:
        epilepsi_logs = []''', content)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
