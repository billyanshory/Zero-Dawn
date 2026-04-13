with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "elif session.get('peran') in ['guru', 'kepala_sekolah'] or session.get('is_admin'):" in line:
        # Avoid inserting twice in case we run it multiple times, but safe since script run once
        lines.insert(i, "        # DESIGN DECISION: Admin/teachers see all nutrition data when no anak_id filter is specified.\n")
        break

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.writelines(lines)
