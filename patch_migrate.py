import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will update the migration code to check if engine dialect is sqlite before executing SQLite specific syntax.
# Also print statement for verification.

search = """        # Manually create indexes for SQLite if they do not exist"""
replace = """        # Manually create indexes for SQLite if they do not exist
        try:
            with db.engine.connect() as con:
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_status_akun ON akun_pengguna (status_akun)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_anak_id ON akun_pengguna (anak_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_epilepsi_log_created_at ON epilepsi_log (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_tantrum_log_student ON tantrum_log (student)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_tantrum_log_created_at ON tantrum_log (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_student_portfolio_student_id ON student_portfolio (student_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_student_portfolio_created_at ON student_portfolio (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_anak_id ON orang_tua_jadwal (anak_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_time ON orang_tua_jadwal (time)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_notified ON orang_tua_jadwal (notified)"))
        except Exception as e:
            app.logger.warning(f"Index creation skipped: {e}")"""

# Wait, I already added it in the previous step. The reason it might not be applying is because db.create_all() does not run if table exists or the exception suppresses it?
# Wait, `db.drop_all()` in test script wasn't working?
# Or maybe the test script failed to run create_all because `con.execute()` in SQLAlchemy 2.0 requires `con.commit()` ? Yes! `db.engine.connect()` requires `.commit()` inside the context block.

new_migration_code = """
        # Manually create indexes for SQLite if they do not exist
        try:
            with db.engine.connect() as con:
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_status_akun ON akun_pengguna (status_akun)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_anak_id ON akun_pengguna (anak_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_epilepsi_log_created_at ON epilepsi_log (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_tantrum_log_student ON tantrum_log (student)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_tantrum_log_created_at ON tantrum_log (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_student_portfolio_student_id ON student_portfolio (student_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_student_portfolio_created_at ON student_portfolio (created_at)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_anak_id ON orang_tua_jadwal (anak_id)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_time ON orang_tua_jadwal (time)"))
                con.execute(db.text("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_notified ON orang_tua_jadwal (notified)"))
                con.commit()
        except Exception as e:
            app.logger.warning(f"Index creation skipped: {e}")
"""

# Let's replace the previous block
content = re.sub(r"        # Manually create indexes for SQLite if they do not exist.*?app.logger.warning\(f\"Index creation skipped: \{e\}\"\)", new_migration_code.strip(), content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Migration patched with commit().")
