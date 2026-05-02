import re

with open("masjid-al-hijrah-72 - alternate - ( idcloudhost - Second Layer of Quality Control - Error Handling & Resilience - v.71 - Opus 4.6 Ex. Think ).py", "r") as f:
    content = f.read()

shohibul_gen_target = """        last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
        if last_record:
            last_num = int(last_record.pin.split('-')[1])
            next_num = last_num + 1
        else:
            next_num = 1
        new_pin = f"{prefix}-{next_num:03d}"
        shohibul = QurbanShohibul(pin=new_pin, jenis_hewan=jenis, nama_shohibul=nama)
        db.session.add(shohibul)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'pin': new_pin, 'message': f'Berhasil meng-generate PIN {new_pin}'})
        else:
            flash(f"Berhasil meng-generate PIN {new_pin}", "success")
            return redirect(url_for('idul_adha_shohibul', q=new_pin))
    except Exception as e:
        db.session.rollback()"""

shohibul_gen_replacement = """        for attempt in range(3):
            last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
            if last_record:
                last_num = int(last_record.pin.split('-')[1])
                next_num = last_num + 1
            else:
                next_num = 1
            new_pin = f"{prefix}-{next_num:03d}"
            shohibul = QurbanShohibul(pin=new_pin, jenis_hewan=jenis, nama_shohibul=nama)
            db.session.add(shohibul)
            try:
                db.session.commit()
                if request.is_json:
                    return jsonify({'success': True, 'pin': new_pin, 'message': f'Berhasil meng-generate PIN {new_pin}'})
                else:
                    flash(f"Berhasil meng-generate PIN {new_pin}", "success")
                    return redirect(url_for('idul_adha_shohibul', q=new_pin))
            except Exception:
                db.session.rollback()
                if attempt == 2:
                    raise
    except Exception as e:
        db.session.rollback()"""

content = content.replace(shohibul_gen_target, shohibul_gen_replacement)

with open("masjid-al-hijrah-72 - alternate - ( idcloudhost - Second Layer of Quality Control - Error Handling & Resilience - v.71 - Opus 4.6 Ex. Think ).py", "w") as f:
    f.write(content)

print("Patched successfully")
