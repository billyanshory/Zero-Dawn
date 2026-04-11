import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """        try:
            data = request.json
            db.session.add(OrangTuaNutrisi(
                anak_id=session.get('anak_id'),
                food_name=validate_str(data.get('food_name'), 255),
                has_allergen=data.get('has_allergen', False)
            ))
            db.session.commit()
            return jsonify({"status": "success"})"""

replacement = """        try:
            data = request.json
            anak_id = session.get('anak_id')
            if anak_id and not db.session.get(Siswa, anak_id):
                return jsonify({'error': 'Data siswa tidak ditemukan'}), 404

            db.session.add(OrangTuaNutrisi(
                anak_id=anak_id,
                food_name=validate_str(data.get('food_name'), 255),
                has_allergen=data.get('has_allergen', False)
            ))
            db.session.commit()
            return jsonify({"status": "success"})"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced ot_nutrisi successfully")
else:
    print("Target ot_nutrisi not found")
