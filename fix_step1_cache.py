file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import re

# 1. Remove epilepsi_logs from index()
idx = content.find("def index():")
end_idx = content.find("def uploaded_file(", idx)
original_index = content[idx:end_idx]

new_index = """def index():
    try:
        verified_alumni_list = TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all()
    except:
        verified_alumni_list = []

    return render_page(HOME_HTML, 'home', content_kwargs={'verified_alumni_list': verified_alumni_list})

@app.route('/uploads/<filename>')
@login_required
"""
content = content.replace(original_index, new_index)

# 2. Add /api/therapy/logs endpoint
new_route = """
@app.route('/api/therapy/logs', methods=['GET'])
@login_required
def api_therapy_logs():
    logs = EpilepsiLog.query.filter_by(user_id=current_user.id).order_by(EpilepsiLog.date.desc()).limit(30).all()
    return jsonify([{'date': l.date.strftime('%Y-%m-%d'), 'pemicu': l.pemicu, 'catatan': l.catatan} for l in logs])

"""
content = content.replace("@app.route('/therapy/log', methods=['POST'])", new_route + "@app.route('/therapy/log', methods=['POST'])")

# 3. Update HOME_HTML to use JS for epilepsi_logs
target_template = """{% for log in epilepsi_logs %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-start">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{{ log.date }}</span>
                        </div>
                        <p class="text-sm font-bold text-gray-800">{{ log.pemicu }}</p>
                        {% if log.catatan %}<p class="text-xs text-gray-500 mt-1 italic">"{{ log.catatan }}"</p>{% endif %}
                    </div>
                </div>
                {% else %}
                <p class="text-center text-gray-400 text-xs py-4">Belum ada data rekaman.</p>
                {% endfor %}"""

replacement_template = """<div id="epilepsi-logs-container">
                    <p class="text-center text-gray-400 text-xs py-4">Memuat data rekaman...</p>
                </div>"""

content = content.replace(target_template, replacement_template)

# 4. Inject JS into refreshCaptcha script block or similar
js_to_inject = """
async function loadEpilepsiLogs() {
    try {
        const res = await fetch('/api/therapy/logs');
        if (!res.ok) return;
        const logs = await res.json();
        const container = document.getElementById('epilepsi-logs-container');
        if (!container) return;

        if (logs.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-400 text-xs py-4">Belum ada data rekaman.</p>';
            return;
        }

        let html = '';
        logs.forEach(log => {
            html += `
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-start mb-3">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">${log.date}</span>
                        </div>
                        <p class="text-sm font-bold text-gray-800">${log.pemicu}</p>
                        ${log.catatan ? `<p class="text-xs text-gray-500 mt-1 italic">"${log.catatan}"</p>` : ''}
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch(e) { console.error(e); }
}
"""

# Find the existing script block we injected for refreshCaptcha
content = content.replace("async function refreshCaptcha() {", js_to_inject + "\nasync function refreshCaptcha() {")

# Update openModal
# Modify openModal inside HOME_HTML
target_open_modal = """        if (id === 'modal-tracer-form' && typeof refreshCaptcha === 'function') { refreshCaptcha(); }"""
replacement_open_modal = """        if (id === 'modal-tracer-form' && typeof refreshCaptcha === 'function') { refreshCaptcha(); }
        if (id === 'modal-terapi-log' && typeof loadEpilepsiLogs === 'function') { loadEpilepsiLogs(); }"""

content = content.replace(target_open_modal, replacement_open_modal)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
