with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """    <p><strong>Pengungkapan ke Pihak Ketiga:</strong> Kami menggunakan layanan pihak ketiga yang mungkin menerima sebagian data IP/User-Agent Anda:</p>"""

replace = """    <p><strong>Backup & Penghapusan:</strong> Permintaan penghapusan akun (Hak Penghapusan UU PDP Art. 9) diproses langsung di basis data aktif. Cadangan terenkripsi (AES-256) yang disimpan oleh penyedia hosting akan terus berisi data yang dihapus selama maksimal 30 hari sebelum siklus rotasi cadangan menghapusnya secara permanen.</p>
    <p><strong>Pengungkapan ke Pihak Ketiga:</strong> Kami menggunakan layanan pihak ketiga yang mungkin menerima sebagian data IP/User-Agent Anda:</p>"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
