import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

routes = """
@app.route('/admin/qurban/distribusi/tandai-selesai/<int:kupon_id>', methods=['POST'])
def admin_qurban_distribusi_tandai_selesai(kupon_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        kupon = DistribusiKupon.query.get(kupon_id)
        if not kupon:
            return jsonify({'error': 'Kupon tidak ditemukan.'}), 404

        if kupon.is_claimed:
            return jsonify({'error': 'Kupon sudah diklaim.'}), 400

        slot = DistribusiSlot.query.get(kupon.slot_id)
        if slot.is_locked:
             return jsonify({'error': 'Slot RT ini sudah dikunci (Locked). Hubungi Admin Utama untuk membuka kunci.'}), 403

        kupon.is_claimed = True
        kupon.claimed_at = datetime.datetime.now()

        # Increment slot distributed count
        slot.distributed_count += 1

        db.session.commit()
        return jsonify({'success': 'Berhasil menandai kupon sebagai selesai.'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error claiming kupon: {e}")
        return jsonify({'error': 'Terjadi kesalahan sistem.'}), 500
"""

insert_target_r = "if __name__ == '__main__':"
if insert_target_r in content:
    content = content.replace(insert_target_r, routes + "\n" + insert_target_r)

with open(filename, "w") as f:
    f.write(content)

print("Injected tandai selesai")
