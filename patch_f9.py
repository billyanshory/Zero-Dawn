with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "elif peran in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):" in line:
        lines.insert(i, "    # DESIGN DECISION: Teachers/admin see all students' chart data when no anak_id filter is specified.\n")
        break

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.writelines(lines)
