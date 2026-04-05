with open("kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "setInterval" in line and "fetch" in line:
        print(f"Line {i+1}: {line.strip()}")
