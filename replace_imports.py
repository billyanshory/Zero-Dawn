import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if line.strip() == "from sqlalchemy import Index":
        new_lines.append("from sqlalchemy.exc import IntegrityError\n")
        new_lines.append("from datetime import time as dt_time\n")

with open(file_path, "w") as f:
    f.writelines(new_lines)
