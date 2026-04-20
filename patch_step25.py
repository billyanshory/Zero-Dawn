with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

guardrail = "# PRIVACY GUARDRAIL: do NOT add @cache.cached or @cache.memoize here without a session-qualified key_prefix — this endpoint returns per-user medical data.\n"

text = text.replace("@app.route('/api/cari-siswa-guru', methods=['GET'])", guardrail + "@app.route('/api/cari-siswa-guru', methods=['GET'])")
text = text.replace("@app.route('/api/unduh-data-saya', methods=['GET'])", guardrail + "@app.route('/api/unduh-data-saya', methods=['GET'])")
text = text.replace("@app.route('/api/hapus-akun-saya', methods=['POST'])", guardrail + "@app.route('/api/hapus-akun-saya', methods=['POST'])")

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)
