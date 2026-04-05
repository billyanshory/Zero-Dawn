import re

file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# =========================================================
# Step 1: CAPTCHA fix
# =========================================================
new_route = """
@app.route('/api/captcha/refresh', methods=['POST'])
@limiter.limit("20 per minute")
def api_captcha_refresh():
    import random
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    session['captcha_a'] = a
    session['captcha_b'] = b
    session['captcha_answer'] = a + b
    return jsonify({'a': a, 'b': b})

"""
content = content.replace("@app.route('/')\n@cache.cached(timeout=30", new_route + "@app.route('/')\n@cache.cached(timeout=30")

idx = content.find('def index():')
if idx != -1:
    end_idx = content.find('try:', idx)
    original_block = content[idx:end_idx]

    new_block = """def index():
    if current_user.is_authenticated:
        epilepsi_logs = EpilepsiLog.query.filter_by(user_id=current_user.id).order_by(EpilepsiLog.date.desc()).limit(30).all()
        logs_display = [{'date': l.date.strftime('%Y-%m-%d'), 'time': '00:00', 'trigger': l.pemicu, 'notes': l.catatan} for l in epilepsi_logs]
    else:
        logs_display = []

    """
    content = content.replace(original_block, new_block)

content = content.replace("content_kwargs={'verified_alumni_list': verified_alumni_list})", "content_kwargs={'verified_alumni_list': verified_alumni_list, 'epilepsi_logs': logs_display})")

html_to_append = """
<script>
async function refreshCaptcha() {
    try {
        const fd = new FormData();
        const csrfToken = document.querySelector('input[name="csrf_token"]');
        if (csrfToken) fd.append('csrf_token', csrfToken.value);
        const res = await fetch('/api/captcha/refresh', {method: 'POST', body: fd});
        const data = await res.json();
        const el = document.getElementById('captcha-question');
        if (el) el.innerText = `Berapa hasil dari ${data.a} + ${data.b}? (CAPTCHA)`;
    } catch(e) { console.error(e); }
}
</script>
"""
content = content.replace('RAMADHAN_DASHBOARD_HTML = """', html_to_append + '\nRAMADHAN_DASHBOARD_HTML = """')

target = 'history.pushState({modal: id}, null, "");'
replacement = "history.pushState({modal: id}, null, \"\");\n        if (id === 'modal-tracer-form' && typeof refreshCaptcha === 'function') { refreshCaptcha(); }"
content = content.replace(target, replacement, 1)

# =========================================================
# Step 2: EpilepsiLog Model and Route
# =========================================================
model_str = """
class EpilepsiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    date = db.Column(db.Date, nullable=False)
    durasi_menit = db.Column(db.Integer, default=0)
    pemicu = db.Column(db.String(255))
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
"""
content = content.replace("class TracerStudy(db.Model):", model_str + "\nclass TracerStudy(db.Model):")

route_str = """
@app.route('/therapy/log', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def therapy_log():
    try:
        date_str = request.form.get('date')
        pemicu = request.form.get('trigger')
        catatan = request.form.get('notes')
        import datetime
        parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        new_log = EpilepsiLog(
            user_id=current_user.id,
            date=parsed_date,
            durasi_menit=0,
            pemicu=pemicu,
            catatan=catatan
        )
        db.session.add(new_log)
        db.session.commit()
        flash("Jurnal kambuh berhasil disimpan.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving therapy log: {e}", exc_info=True)
        flash("Terjadi kesalahan. Pastikan format tanggal benar (YYYY-MM-DD).", "error")
    return redirect(request.referrer or url_for('index'))
"""
content = content.replace("@app.route('/manifest.json')", route_str + "\n@app.route('/manifest.json')")

# =========================================================
# Step 3: Prayer Times
# =========================================================
content = content.replace("t += tzone - 8 # Base is calculated relative to GMT, we just add timezone", "t += tzone")

old_except = """    except Exception as e:
        app.logger.error(f"Error fetching Imsakiyah API: {e}", exc_info=True)
        # Fallback empty or local calculation if needed, but user requested API specifically.

    return schedule"""

new_except = """    except Exception as e:
        app.logger.error(f"Error fetching Imsakiyah API: {e}", exc_info=True)
        return []

    return schedule"""
content = content.replace(old_except, new_except)

# Fix Javascript interval bug: `setInterval(fetchPrayerTimes, 1000)` might exist in FITUR_MASJID_HTML
target_interval = "setInterval(fetchPrayerTimes, 1000);"
replacement_interval = """document.addEventListener('DOMContentLoaded', async () => { await fetchPrayerTimes(); setInterval(updateCountdown, 1000); });"""
# The user explicitly said this is what needs to happen. But maybe it's not exactly that string. Let's look for `setInterval(fetchPrayerTimes`
if "setInterval(fetchPrayerTimes" in content:
    content = re.sub(r'setInterval\(fetchPrayerTimes, 1000\);?', replacement_interval, content)
else:
    # Actually wait, let me look specifically at the Prayer logic in HOME_HTML or FITUR_MASJID_HTML. I'll search and replace using bash first if needed. Let me comment this out here and do it safely below.
    pass

# =========================================================
# Step 4: Seed admin
# =========================================================
target = """    except Exception as e:
        return f"Error: {e}"
"""
replacement = """    except Exception as e:
        app.logger.error(f"Seed admin error: {e}", exc_info=True)
        return "Terjadi kesalahan. Periksa log server.", 500
"""
content = content.replace(target, replacement)

# =========================================================
# Step 5: Deprecated .get()
# =========================================================
target = "pmb = PendaftaranPMB.query.with_for_update().get(item_id)"
replacement = "pmb = db.session.query(PendaftaranPMB).with_for_update().filter_by(id=item_id).first()"
content = content.replace(target, replacement)

# =========================================================
# Step 6: Pagination UI and _fetch_tu_data()
# =========================================================
target_func = """def _fetch_tu_data():
    try:
        pending_users = User.query.filter_by(status_akademik='Menunggu Verifikasi').order_by(User.id.desc()).all()
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).all(),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).all(),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).all(),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all(),
            pending_users
        )"""

replacement_func = """def _fetch_tu_data():
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        pending_users = User.query.filter_by(status_akademik='Menunggu Verifikasi').order_by(User.id.desc()).all()
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).paginate(page=page, per_page=50),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).paginate(page=page, per_page=50),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).paginate(page=page, per_page=50),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all(),
            pending_users
        )"""

content = content.replace(target_func, replacement_func)

# Extract RAMADHAN_DASHBOARD_HTML and process it separately
start_idx = content.find('RAMADHAN_DASHBOARD_HTML = """')
end_idx = content.find('"""\n\nIRMA_STYLES', start_idx)

if start_idx != -1 and end_idx != -1:
    ramadhan_html = content[start_idx:end_idx]

    ramadhan_html = ramadhan_html.replace("{% for item in pmb_list %}", "{% for item in pmb_list.items %}")
    ramadhan_html = ramadhan_html.replace("{% for item in tagihan_list %}", "{% for item in tagihan_list.items %}")
    ramadhan_html = ramadhan_html.replace("{% for item in akun_list %}", "{% for item in akun_list.items %}")

    pmb_pagination = """                    {% endfor %}
                </div>
                <div class="p-4 flex justify-between gap-2 mt-4 bg-white/5 rounded-xl border border-white/10">
                    <div>
                        {% if pmb_list.has_prev %}
                        <a href="?open=modal-verifikasi-pmb&page={{ pmb_list.prev_num }}" class="text-gold font-bold text-xs hover:text-white transition">&laquo; Sebelumnya</a>
                        {% endif %}
                    </div>
                    <div>
                        {% if pmb_list.has_next %}
                        <a href="?open=modal-verifikasi-pmb&page={{ pmb_list.next_num }}" class="text-gold font-bold text-xs hover:text-white transition">Berikutnya &raquo;</a>
                        {% endif %}
                    </div>
                </div>"""
    ramadhan_html = ramadhan_html.replace("""                    {% endfor %}
                </div>""", pmb_pagination, 1)

    tagihan_pagination = """                {% endfor %}
            </div>
            <div class="p-4 flex justify-between gap-2 mt-4 bg-white/5 rounded-xl border border-white/10">
                <div>
                    {% if tagihan_list.has_prev %}
                    <a href="?open=modal-verifikasi-pembayaran&page={{ tagihan_list.prev_num }}" class="text-gold font-bold text-xs hover:text-white transition">&laquo; Sebelumnya</a>
                    {% endif %}
                </div>
                <div>
                    {% if tagihan_list.has_next %}
                    <a href="?open=modal-verifikasi-pembayaran&page={{ tagihan_list.next_num }}" class="text-gold font-bold text-xs hover:text-white transition">Berikutnya &raquo;</a>
                    {% endif %}
                </div>
            </div>"""
    ramadhan_html = ramadhan_html.replace("""                {% endfor %}
            </div>""", tagihan_pagination, 1)

    akun_pagination = """                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <div class="p-4 flex justify-between gap-2 mt-4 bg-white/5 rounded-xl border border-white/10">
                <div>
                    {% if akun_list.has_prev %}
                    <a href="?open=modal-manajemen-sivitas&page={{ akun_list.prev_num }}" class="text-gold font-bold text-xs hover:text-white transition">&laquo; Sebelumnya</a>
                    {% endif %}
                </div>
                <div>
                    {% if akun_list.has_next %}
                    <a href="?open=modal-manajemen-sivitas&page={{ akun_list.next_num }}" class="text-gold font-bold text-xs hover:text-white transition">Berikutnya &raquo;</a>
                    {% endif %}
                </div>
            </div>"""
    ramadhan_html = ramadhan_html.replace("""                        {% endfor %}
                    </tbody>
                </table>
            </div>""", akun_pagination, 1)

    content = content[:start_idx] + ramadhan_html + content[end_idx:]

# =========================================================
# Step 7: Input validation for tu_jadwal
# =========================================================
target = """def tu_jadwal():
    try:
        new_jadwal = JadwalKuliah("""

replacement = """def tu_jadwal():
    try:
        hari = request.form.get('hari', '')
        jam = request.form.get('jam', '')

        valid_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']
        if hari not in valid_hari:
            flash("Hari tidak valid", "error")
            return "Hari tidak valid", 400

        import re
        if not re.match(r'^\\d{2}:\\d{2}\\s*-\\s*\\d{2}:\\d{2}$', jam):
            flash("Format jam tidak valid (Gunakan format HH:MM - HH:MM)", "error")
            return "Format jam tidak valid", 400

        new_jadwal = JadwalKuliah("""
content = content.replace(target, replacement)

# =========================================================
# Step 8: Remove orphan pass statements
# =========================================================
# Lines specified by previous grep output: 357, 386, 547, 769, 1305, 1452, 1908, 1934, 1959, 2035, 2153
lines_to_remove = [357, 386, 547, 769, 1305, 1452, 1908, 1934, 1959, 2035, 2153]

# Let's verify by just regexing lines that only contain "pass" EXCEPT those directly following "except:"
# Actually, I can split lines, delete empty pass lines IF the previous line is not `except:` or `except Exception as e:`
lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "pass":
        prev_line = lines[i-1].strip() if i > 0 else ""
        if prev_line.startswith("except") or prev_line.startswith("def") or prev_line.startswith("if") or prev_line.startswith("else") or prev_line.startswith("elif") or prev_line.startswith("for") or prev_line.startswith("while") or prev_line.startswith("try:"):
            new_lines.append(line) # Keep it, it's a structural pass
        else:
            # It's an orphan pass
            pass # Remove it
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
