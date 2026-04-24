import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

route_lacak_update = """
@app.route('/qurban/lacak', methods=['GET', 'POST'])
def qurban_lacak():
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'success': False, 'error': 'Invalid request format'}), 400

            pin = data.get('pin', '').strip().upper()
            if not pin:
                return jsonify({'success': False, 'error': 'PIN wajib diisi'}), 400

            animal = QurbanAnimal.query.filter_by(pin=pin).first()
            if not animal:
                return jsonify({'success': False, 'error': 'PIN Tidak Ditemukan. Silakan periksa kembali PIN Anda.'})

            return jsonify({
                'success': True,
                'data': {
                    'animal_type': animal.animal_type,
                    'queue_number': animal.queue_number,
                    'sohibul_name': animal.sohibul_name,
                    'status': animal.status
                }
            })
        except Exception as e:
            app.logger.error(f"Error looking up PIN: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Terjadi kesalahan sistem saat mencari data.'}), 500

    # GET request just serves the page
    rendered_content = render_template_string(IDUL_ADHA_LACAK_HTML, is_admin=session.get('is_admin', False))
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())
"""

content = re.sub(
    r"@app\.route\('/qurban/lacak', methods=\['GET'\]\).*?def qurban_lacak\(\):.*?return render_template_string\(BASE_LAYOUT.*?\)",
    route_lacak_update.strip(),
    content,
    flags=re.DOTALL
)

route_pembagian_update = """
@app.route('/qurban/pembagian/cek', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def qurban_pembagian_cek():
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'found': False, 'message': 'Format request tidak valid.'}), 400

            nik = data.get('nik', '').strip()
            coupon_number = data.get('coupon_number', '').strip().upper()

            if not nik.isdigit() or len(nik) != 16:
                return jsonify({'found': False, 'message': 'Format NIK tidak valid. Harus 16 digit angka.'}), 400

            kupon = DistribusiKupon.query.filter_by(nik=nik, coupon_number=coupon_number).first()
            if not kupon:
                return jsonify({'found': False, 'message': 'Data tidak ditemukan. Silakan hubungi panitia.'})

            slot = DistribusiSlot.query.get(kupon.slot_id)
            if not slot:
                return jsonify({'found': False, 'message': 'Slot distribusi tidak ditemukan.'})

            return jsonify({
                'found': True,
                'data': {
                    'nik': kupon.nik,
                    'coupon_number': kupon.coupon_number,
                    'rt_identifier': slot.rt_identifier,
                    'time_start': slot.time_start,
                    'time_end': slot.time_end,
                    'is_claimed': kupon.is_claimed,
                    'quota_left': slot.total_quota - slot.distributed_count
                }
            })
        except Exception as e:
            app.logger.error(f"Error checking kupon: {e}", exc_info=True)
            return jsonify({'found': False, 'message': 'Terjadi kesalahan sistem saat mencari data.'}), 500

    # GET request just serves the page
    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_CEK_HTML, is_admin=session.get('is_admin', False))
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())
"""

content = re.sub(
    r"@app\.route\('/qurban/pembagian/cek', methods=\['GET', 'POST'\]\).*?def qurban_pembagian_cek\(\):.*?return render_template_string\(BASE_LAYOUT.*?\)",
    route_pembagian_update.strip(),
    content,
    flags=re.DOTALL
)

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
