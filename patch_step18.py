with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        if profil:
            profil_dict = {c.name: getattr(profil, c.name) for c in profil.__table__.columns if c.name not in ('id', 'siswa_id', 'kondisi_warna')}
            data['profil_medis'] = profil_dict

    return jsonify(data)"""

replace = """        if profil:
            profil_dict = {c.name: getattr(profil, c.name) for c in profil.__table__.columns if c.name not in ('id', 'siswa_id', 'kondisi_warna')}
            data['profil_medis'] = profil_dict

    consents = ConsentRecord.query.filter_by(akun_id=akun.id).all()
    if consents:
        data['consent_records'] = [{
            'policy_version': c.policy_version,
            'granted_at': c.granted_at.isoformat() if c.granted_at else None,
            'withdrawn_at': c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            'scope': c.scope
        } for c in consents]

    return jsonify(data)"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
