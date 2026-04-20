with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

# Replace inner imports and hoist
search_import_json_1 = "        import json\n        prior_snapshot = json.dumps(prior_dict, default=str, ensure_ascii=False)"
replace_import_json_1 = "        prior_snapshot = _json_module.dumps(prior_dict, default=str, ensure_ascii=False)"

search_import_json_2 = """    import json
    new_dict = {c.name: getattr(profil, c.name) for c in profil.__table__.columns}
    new_snapshot = json.dumps(new_dict, default=str, ensure_ascii=False)"""
replace_import_json_2 = """    new_dict = {c.name: getattr(profil, c.name) for c in profil.__table__.columns}
    new_snapshot = _json_module.dumps(new_dict, default=str, ensure_ascii=False)"""

search_import_json_3 = "import json"
replace_import_json_3 = "import json as _json_module"


# Separate transaction
search_transaction = """    db.session.add(audit_row)

    try:
        db.session.commit()
        return jsonify({'status': 'success'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Data duplikat terdeteksi. Silakan periksa kembali.'}), 409
    except OperationalError:
        db.session.rollback()
        return jsonify({'error': 'Koneksi database terganggu. Silakan coba lagi.'}), 503
    except Exception as e:
        db.session.rollback()
        app.logger.error('Medical profile update failed', exc_info=True)
        return jsonify({'error': 'Gagal menyimpan data medis.'}), 500"""

replace_transaction = """    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Data duplikat terdeteksi. Silakan periksa kembali.'}), 409
    except OperationalError:
        db.session.rollback()
        return jsonify({'error': 'Koneksi database terganggu. Silakan coba lagi.'}), 503
    except Exception as e:
        db.session.rollback()
        app.logger.error('Medical profile update failed', exc_info=True)
        return jsonify({'error': 'Gagal menyimpan data medis.'}), 500

    try:
        db.session.add(audit_row)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.warning("Failed to insert ProfilMedisSiswaAudit record", exc_info=True)

    return jsonify({'status': 'success'})"""

text = text.replace(search_import_json_1, replace_import_json_1)
text = text.replace(search_import_json_2, replace_import_json_2)
text = text.replace(search_import_json_3, replace_import_json_3, 1) # Only first one!
text = text.replace(search_transaction, replace_transaction)

# Add audit endpoint
search_audit_route = """@app.route('/api/cari-siswa-guru', methods=['GET'])"""

replace_audit_route = """@app.route('/api/profil-medis/<int:siswa_id>/audit', methods=['GET'])
@limiter.limit("30 per hour")
@require_auth(roles=[ROLE_KEPALA_SEKOLAH])
def get_profil_medis_audit(siswa_id: int) -> Response | str | tuple[Response, int]:
    audits = ProfilMedisSiswaAudit.query.filter_by(siswa_id=siswa_id).order_by(ProfilMedisSiswaAudit.changed_at.desc()).limit(50).all()
    result = []
    for a in audits:
        result.append({
            'changed_at': a.changed_at.isoformat() if a.changed_at else None,
            'changed_by': a.changed_by,
            'peran': a.changed_by_peran,
            'action': a.action,
            'request_id': a.request_id
        })
    return jsonify(result)

@app.route('/api/cari-siswa-guru', methods=['GET'])"""

text = text.replace(search_audit_route, replace_audit_route)

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)
print("Success")
