import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

route_stats = """
@app.route('/api/qurban/stats', methods=['GET'])
def api_qurban_stats():
    try:
        stats = QurbanStats.query.first()
        if not stats:
            return jsonify({
                'success': True,
                'total_cattle': 0,
                'total_goat': 0,
                'total_meat_weight_kg': 0.0,
                'total_packages_prepared': 0,
                'total_packages_distributed': 0
            })

        return jsonify({
            'success': True,
            'total_cattle': stats.total_cattle,
            'total_goat': stats.total_goat,
            'total_meat_weight_kg': stats.total_meat_weight_kg,
            'total_packages_prepared': stats.total_packages_prepared,
            'total_packages_distributed': stats.total_packages_distributed
        })
    except Exception as e:
        app.logger.error(f"Error fetching Qurban stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to fetch data'}), 500
"""

content = re.sub(
    r"@app\.route\('/api/qurban/stats', methods=\['GET'\]\).*?def api_qurban_stats\(\):.*?return jsonify\(\{'error': 'Failed to fetch data'\}\), 500",
    route_stats.strip(),
    content,
    flags=re.DOTALL
)

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
