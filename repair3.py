import re

with open("sekolah_luar_biasa.py", "r") as f:
    content = f.read()

def wrap_commit(func_snippet, error_handler):
    global content
    content = content.replace(
        func_snippet + "\n        db.session.commit()",
        func_snippet + "\n        try:\n            db.session.commit()\n        except Exception as e:\n            db.session.rollback()\n            app.logger.error('Database commit error', exc_info=True)\n" + "            " + error_handler
    )

wrap_commit("akun.status_akun = 'disetujui'", "pass")
wrap_commit("db.session.delete(akun)", "pass")


content = content.replace(
"""    profil.tambahan_info = data.get('tambahan_info', profil.tambahan_info)

    db.session.commit()
    return jsonify({'status': 'success'})""",
"""    profil.tambahan_info = data.get('tambahan_info', profil.tambahan_info)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({'status': 'success'})"""
)


with open("sekolah_luar_biasa.py", "w") as f:
    f.write(content)
