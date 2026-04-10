import re

with open('app.py', 'r') as f:
    content = f.read()

# Let's ensure these specific fetch calls have the header if they are POST

# 1. /guru/tantrum
old1 = """            const res = await fetch('/guru/tantrum', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},"""
new1 = """            const res = await fetch('/guru/tantrum', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old1, new1)

# 2. /guru/iep
old2 = """            const res = await fetch('/guru/iep', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},"""
new2 = """            const res = await fetch('/guru/iep', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old2, new2)

# 3. /guru/reaction
old3 = """            await fetch('/guru/reaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},"""
new3 = """            await fetch('/guru/reaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old3, new3)

# 4. /guru/kognitif/bentuk
old4 = """            await fetch('/guru/kognitif/bentuk', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},"""
new4 = """            await fetch('/guru/kognitif/bentuk', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old4, new4)

# 5. /guru/kognitif/emosi
old5 = """            await fetch('/guru/kognitif/emosi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},"""
new5 = """            await fetch('/guru/kognitif/emosi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old5, new5)

# 6. /brankas_unlock
old6 = """                        fetch('/brankas_unlock', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },"""
new6 = """                        fetch('/brankas_unlock', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                            },"""
content = content.replace(old6, new6)

# 7. /orang-tua/api/subscribe
old7 = """                await fetch('/orang-tua/api/subscribe', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},"""
new7 = """                await fetch('/orang-tua/api/subscribe', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},"""
content = content.replace(old7, new7)


# Now fix APIs to have rollback
# save_ot_buku
old_buku = """@app.route('/orang-tua/api/buku', methods=['POST'])
@limiter.limit("20 per minute")
def save_ot_buku():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.json
        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=data.get('mood'),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=data.get('morning_behavior')
        ))
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": "Failed"}), 500"""
new_buku = """@app.route('/orang-tua/api/buku', methods=['POST'])
@limiter.limit("20 per minute")
def save_ot_buku():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.json
        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=data.get('mood'),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=data.get('morning_behavior')
        ))
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed"}), 500"""
content = content.replace(old_buku, new_buku)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching.")
