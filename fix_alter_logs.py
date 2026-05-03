import re

filename = "masjid-al-hijrah-74 - alternate - ( idcloudhost - Third Layer of Quality Control - Input Validation & Data Integrity - v.73 - Opus 4.6 Ex. Think - Second Effort).py"

with open(filename, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "except Exception as e: app.logger.error" in line and "if 'already exists' not in str(e).lower() and 'duplicate column' not in str(e).lower():" not in line:
        pass # this won't match exactly because we might have split lines
    new_lines.append(line)
