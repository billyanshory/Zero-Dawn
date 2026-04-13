with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'return "Unauthorized", 403' in line:
        if i+1 in [4671, 5189, 5440, 10613]: # the line numbers got shifted by +1 because of F11 fix, +1 because of imports
             lines[i] = line.replace('return "Unauthorized", 403', "return jsonify({'error': 'Unauthorized'}), 403")
        # Check around line numbers to make it robust
        if 4668 <= i <= 4672 or 5186 <= i <= 5191 or 5437 <= i <= 5442 or 10610 <= i <= 10615:
             lines[i] = line.replace('return "Unauthorized", 403', "return jsonify({'error': 'Unauthorized'}), 403")

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.writelines(lines)
