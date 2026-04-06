import re

file_path = "sekolah-luar-biasa-56 ( idcloudhost - Fourth Layer of Quality Control - Latency UX ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

index_block_search = r"""        try:
            with db.engine.connect() as con:
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_status_akun ON akun_pengguna \(status_akun\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_akun_pengguna_anak_id ON akun_pengguna \(anak_id\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_epilepsi_log_created_at ON epilepsi_log \(created_at\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_tantrum_log_student ON tantrum_log \(student\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_tantrum_log_created_at ON tantrum_log \(created_at\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_student_portfolio_student_id ON student_portfolio \(student_id\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_student_portfolio_created_at ON student_portfolio \(created_at\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_anak_id ON orang_tua_jadwal \(anak_id\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_time ON orang_tua_jadwal \(time\)"\)\)
                con.execute\(db.text\("CREATE INDEX IF NOT EXISTS idx_orang_tua_jadwal_notified ON orang_tua_jadwal \(notified\)"\)\)
                con.commit\(\)
        except Exception as e:
            app.logger.warning\(f"Index creation skipped: \{e\}"\)"""

replacement = """        # Manually create indexes with compatibility check for older MySQL
        indexes_to_create = [
            ("akun_pengguna", "idx_akun_pengguna_status_akun", "status_akun"),
            ("akun_pengguna", "idx_akun_pengguna_anak_id", "anak_id"),
            ("epilepsi_log", "idx_epilepsi_log_created_at", "created_at"),
            ("tantrum_log", "idx_tantrum_log_student", "student"),
            ("tantrum_log", "idx_tantrum_log_created_at", "created_at"),
            ("student_portfolio", "idx_student_portfolio_student_id", "student_id"),
            ("student_portfolio", "idx_student_portfolio_created_at", "created_at"),
            ("orang_tua_jadwal", "idx_orang_tua_jadwal_anak_id", "anak_id"),
            ("orang_tua_jadwal", "idx_orang_tua_jadwal_time", "time"),
            ("orang_tua_jadwal", "idx_orang_tua_jadwal_notified", "notified")
        ]

        try:
            with db.engine.connect() as con:
                for table_name, index_name, column_name in indexes_to_create:
                    try:
                        # Check if index exists using information_schema
                        check_query = db.text("SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = :table_name AND index_name = :index_name")
                        result = con.execute(check_query, {"table_name": table_name, "index_name": index_name}).scalar()

                        if result == 0:
                            con.execute(db.text(f"CREATE INDEX {index_name} ON {table_name} ({column_name})"))
                    except Exception as inner_e:
                        app.logger.warning(f"Failed to create index {index_name} on {table_name}: {inner_e}")
                con.commit()
        except Exception as e:
            app.logger.warning(f"Index creation skipped: {e}")"""

if re.search(index_block_search, content):
    new_content = re.sub(index_block_search, replacement, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced successfully.")
else:
    print("Could not find block to replace.")
