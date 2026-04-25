with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

content = content.replace(
    "if not nik.isdigit() or len(nik) != 16:\n                return jsonify({'found': False, 'message': 'Format NIK tidak valid. Harus 16 digit angka.'}), 400",
    "if not nik:\n                return jsonify({'found': False, 'message': 'Nama Lengkap Kepala Keluarga tidak boleh kosong.'}), 400"
)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
