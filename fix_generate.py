with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

content = content.replace(
    "if not nik or len(nik) != 16 or not nik.isdigit():\n            return jsonify({'success': False, 'error': 'NIK tidak valid'}), 400",
    "if not nik:\n            return jsonify({'success': False, 'error': 'Nama tidak valid'}), 400"
)

content = content.replace(
    "'error': 'NIK sudah terdaftar'",
    "'error': 'Nama sudah terdaftar'"
)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
