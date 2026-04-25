import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Route update for PIN generation
pin_search = """        name = data.get('name', '').strip()
        animal_type = data.get('type', '').strip()

        if not name or not animal_type:
            return jsonify({'success': False, 'error': 'Nama dan Jenis Hewan wajib diisi'}), 400

        pin = secrets.token_hex(3).upper()

        animal = QurbanAnimal(
            animal_type=animal_type,"""

pin_replace = """        name = data.get('name', '').strip()
        animal_type = data.get('type', '').strip()

        if not name or not animal_type:
            return jsonify({'success': False, 'error': 'Nama dan Jenis Hewan wajib diisi'}), 400

        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        pin = ''.join(secrets.choice(alphabet) for i in range(6))

        animal = QurbanAnimal(
            animal_type=animal_type,"""

content = content.replace(pin_search, pin_replace)

# Admin Panel Container Update for LACAK HTML
lacak_search = """<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20 flex flex-col items-center justify-center p-4">
    <!-- Card Container -->

            <!-- ADMIN PIN PANEL -->
            {% if is_admin %}
            <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-red-100 mb-8 w-full max-w-xl mx-auto" id="admin-pin-panel">"""

lacak_replace = """<div class="min-h-screen bg-[#F5F0E8] font-sans pt-24 md:pt-28 pb-20 flex flex-col items-center p-4">
    <!-- Card Container -->

            <!-- ADMIN PIN PANEL -->
            {% if is_admin %}
            <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-red-100 mb-8 w-full max-w-xl mx-auto" id="admin-pin-panel">"""

content = content.replace(lacak_search, lacak_replace)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
