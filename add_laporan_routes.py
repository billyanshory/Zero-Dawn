import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

routes = """
@app.route('/idul-adha/laporan')
def idul_adha_laporan():
    rendered_content = render_template_string(IDUL_ADHA_LAPORAN_HTML,
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())

@app.route('/api/qurban/stats', methods=['GET'])
def api_qurban_stats():
    try:
        stats = QurbanStats.query.first()
        if not stats:
            return jsonify({
                'total_cattle': 0,
                'total_goat': 0,
                'total_meat_weight_kg': 0.0,
                'total_packages_prepared': 0,
                'total_packages_distributed': 0
            })

        return jsonify({
            'total_cattle': stats.total_cattle,
            'total_goat': stats.total_goat,
            'total_meat_weight_kg': stats.total_meat_weight_kg,
            'total_packages_prepared': stats.total_packages_prepared,
            'total_packages_distributed': stats.total_packages_distributed
        })
    except Exception as e:
        app.logger.error(f"Error fetching Qurban stats: {e}")
        return jsonify({'error': 'Failed to fetch data'}), 500

@app.route('/admin/qurban/stats', methods=['POST'])
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

    return redirect(url_for('idul_adha_laporan'))
"""

with open(filename, "r") as f:
    content = f.read()

# Insert before "if __name__ == '__main__':"
insert_target = "if __name__ == '__main__':"
if insert_target in content:
    content = content.replace(insert_target, routes + "\n" + insert_target)
    with open(filename, "w") as f:
        f.write(content)
    print("Routes injected.")
else:
    print("Could not inject.")
