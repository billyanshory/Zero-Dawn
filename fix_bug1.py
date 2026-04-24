import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fix Bug 1: Laporan Qurban Admin Save
# In the form, add id="admin-qurban-form" and change button type
content = content.replace(
    '<form action="/admin/qurban/stats" method="POST" class="space-y-4">',
    '<form id="admin-qurban-form" class="space-y-4">'
)
content = content.replace(
    '<button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">',
    '<button type="button" onclick="submitQurbanStats(event)" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">'
)

js_addition = """
    async function submitQurbanStats(e) {
        if(e) e.preventDefault();
        const form = document.getElementById('admin-qurban-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const res = await fetch('/admin/qurban/stats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': data.csrf_token
                },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if(res.ok && result.success) {
                alert("Data berhasil disimpan");
                fetchStats();
            } else {
                throw new Error(result.error || "Gagal menyimpan data");
            }
        } catch(err) {
            alert(err.message);
        }
    }
"""

content = content.replace(
    '// Initial fetch',
    js_addition + '\n    // Initial fetch'
)

# Route updates for JSON
route_update = """@app.route('/admin/qurban/stats', methods=['POST'])
def admin_qurban_stats():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

        stats = QurbanStats.query.first()
        if not stats:
            stats = QurbanStats()
            db.session.add(stats)

        stats.total_cattle = int(data.get('total_cattle', 0))
        stats.total_goat = int(data.get('total_goat', 0))
        stats.total_meat_weight_kg = float(data.get('total_meat_weight_kg', 0.0))
        stats.total_packages_prepared = int(data.get('total_packages_prepared', 0))
        stats.total_packages_distributed = int(data.get('total_packages_distributed', 0))

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving Qurban stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal server'}), 500"""

old_route = """@app.route('/admin/qurban/stats', methods=['POST'])
def admin_qurban_stats():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        stats = QurbanStats.query.first()
        if not stats:
            stats = QurbanStats()
            db.session.add(stats)

        stats.total_cattle = int(request.form.get('total_cattle', 0))
        stats.total_goat = int(request.form.get('total_goat', 0))
        stats.total_meat_weight_kg = float(request.form.get('total_meat_weight_kg', 0.0))
        stats.total_packages_prepared = int(request.form.get('total_packages_prepared', 0))
        stats.total_packages_distributed = int(request.form.get('total_packages_distributed', 0))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving Qurban stats: {e}")

    return redirect(url_for('idul_adha_laporan'))"""

content = content.replace(old_route, route_update)

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
