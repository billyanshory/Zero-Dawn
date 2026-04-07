import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r'@app\.route\(\'/slb/tunalaras\', methods=\[\'GET\', \'POST\'\]\).*?active_page=\'slb\', content=SLB_TUNALARAS_HTML, history=history, theme=\{\'nav_bg\': \'bg-teal-100\', \'title_text\': \'text-teal-800\'\}, is_admin=session\.get\(\'is_admin\', False\), settings=get_settings\(\)\)',
r'''@app.route('/slb/tunalaras', methods=['GET', 'POST'])
def slb_tunalaras():
    if request.method == 'POST':
        try:
            emotion = request.form['emotion']
            anak_id = session.get('anak_id') if session.get('peran') == 'orang_tua' else None
            db.session.add(EmotionJournal(emotion=emotion, anak_id=anak_id))
            db.session.commit()
            return redirect(url_for('slb_tunalaras'))
        except Exception as e:
            db.session.rollback()
            return "Terjadi kesalahan saat memproses data. Silakan coba lagi.", 500

    q = EmotionJournal.query
    if session.get('peran') == 'orang_tua' and session.get('anak_id'):
        q = q.filter_by(anak_id=session.get('anak_id')).limit(20)
    else:
        q = q.limit(5)
    history = q.order_by(EmotionJournal.date.desc()).all()

    rendered_tunalaras = render_template_string(SLB_TUNALARAS_HTML, history=history, csrf_token=csrf_token, peran=session.get('peran',''), anak_id=session.get('anak_id'))
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=rendered_tunalaras, theme={'nav_bg': 'bg-teal-100', 'title_text': 'text-teal-800'}, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/api/tunalaras/guru-monitor')
def api_tunalaras_guru_monitor():
    if session.get('peran') not in ['guru', 'kepala_sekolah']:
        return jsonify({'error': 'Unauthorized'}), 403
    q = request.args.get('q', '').lower()

    entries = db.session.query(EmotionJournal).filter(EmotionJournal.anak_id != None).all()
    grouped = {}
    for e in entries:
        if e.anak_id not in grouped: grouped[e.anak_id] = []
        grouped[e.anak_id].append(e)

    results = []
    for a_id, evs in grouped.items():
        evs.sort(key=lambda x: x.date, reverse=True)
        siswa = db.session.get(Siswa, a_id)
        if not siswa: continue
        if q and q not in siswa.nama.lower(): continue
        parent = AkunPengguna.query.filter_by(anak_id=a_id, peran='orang_tua').first()
        parent_name = parent.nama_lengkap if parent else "Unknown"

        recent_emotions = [{"emotion": x.emotion, "date": x.date.strftime('%Y-%m-%d %H:%M') if x.date else ''} for x in evs[:3]]
        results.append({
            "parent_name": parent_name,
            "student_name": siswa.nama,
            "recent_emotions": recent_emotions
        })
    return jsonify(results)''', content, flags=re.DOTALL)

content = re.sub(r'<div class="mt-12">\n            <h3 class="font-bold text-emerald-800 mb-4 pl-2 border-l-4 border-emerald-500">Riwayat Perasaan</h3>.*?</div>\n        </div>',
r'''{% if peran == 'orang_tua' or peran == 'kepala_sekolah' %}
        <div class="mt-12">
            <h3 class="font-bold text-emerald-800 mb-4 pl-2 border-l-4 border-emerald-500">Riwayat Perasaan</h3>
            <div class="space-y-3">
                {% for entry in history %}
                <div class="bg-white p-4 rounded-2xl shadow-sm flex justify-between items-center border border-emerald-50">
                    <span class="font-bold text-emerald-700">{{ entry.emotion }}</span>
                    <span class="text-xs text-emerald-600 font-medium bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-100">{{ entry.date.strftime('%Y-%m-%d %H:%M') if entry.date else '' }}</span>
                </div>
                {% else %}
                <p class="text-center text-emerald-500/70 text-sm py-4 italic">Belum ada catatan emosi.</p>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if peran == 'guru' %}
        <div class="mt-8 bg-white p-4 rounded-2xl shadow-sm border border-emerald-50">
            <h3 class="font-bold text-emerald-800 mb-4 pl-2 border-l-4 border-emerald-500">Monitor Jurnal Emosi Siswa</h3>
            <input type="text" id="guru-monitor-search" placeholder="Cari nama siswa..." class="w-full bg-emerald-50 border border-emerald-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 mb-4" oninput="fetchGuruMonitor()">
            <div id="guru-monitor-results" class="space-y-3 max-h-64 overflow-y-auto"></div>
        </div>
        <script>
        function fetchGuruMonitor() {
            const q = document.getElementById('guru-monitor-search').value;
            fetch('/api/tunalaras/guru-monitor?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('guru-monitor-results');
                    container.innerHTML = '';
                    if(data.length === 0) {
                        container.innerHTML = '<p class="text-center text-emerald-500/70 text-sm py-4 italic">Belum ada data jurnal emosi.</p>';
                        return;
                    }
                    data.forEach(item => {
                        let html = `
                        <div class="p-3 border border-emerald-100 rounded-xl bg-emerald-50/50">
                            <div class="flex justify-between items-center mb-2">
                                <div>
                                    <h4 class="font-bold text-emerald-800 text-sm">${item.student_name}</h4>
                                    <p class="text-[10px] text-emerald-600 font-medium">Ortu: ${item.parent_name}</p>
                                </div>
                            </div>
                            <div class="flex gap-2 flex-wrap">`;

                        item.recent_emotions.forEach(emo => {
                            html += `<span class="bg-white border border-emerald-100 px-2 py-1 rounded-lg text-xs font-bold text-emerald-700 shadow-sm">${emo.emotion} <span class="text-[9px] text-emerald-500 ml-1 font-normal">${emo.date}</span></span>`;
                        });

                        html += `</div></div>`;
                        container.innerHTML += html;
                    });
                });
        }
        document.addEventListener('DOMContentLoaded', fetchGuruMonitor);
        </script>
        {% endif %}''', content, flags=re.DOTALL)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
