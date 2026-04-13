with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def vapid_public_key():" in line:
        lines[i] = """def vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        return jsonify({'error': 'Push notifications not configured'}), 503\n"""
        break

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.writelines(lines)
