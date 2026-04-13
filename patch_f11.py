with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

content = content.replace("@app.route('/uploads/<filename>')\ndef uploaded_file(filename):", "# ACCEPTED RISK: UUID filenames prevent enumeration. Public access needed for /galeri images.\n@app.route('/uploads/<filename>')\ndef uploaded_file(filename):")

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
