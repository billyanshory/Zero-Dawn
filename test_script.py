import sys

filename = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filename, "r") as f:
    lines = f.readlines()

print("BUG-003 (render_template_string calls):")
for i, line in enumerate(lines):
    if "render_template_string(" in line:
        print(f"{i + 1}: {line.strip()}")

print("\nBUG-012 (Tailwind CDN):")
for i, line in enumerate(lines):
    if "tailwindcss.com" in line:
        print(f"{i + 1}: {line.strip()}")

print("\nBUG-013 (Google Fonts):")
for i, line in enumerate(lines):
    if "fonts.googleapis.com" in line:
        print(f"{i + 1}: {line.strip()}")

print("\nBUG-014 (Font Awesome):")
for i, line in enumerate(lines):
    if "font-awesome" in line:
        print(f"{i + 1}: {line.strip()}")

print("\nBUG-019 (backdrop-filter):")
for i, line in enumerate(lines):
    if "backdrop-filter" in line:
        print(f"{i + 1}: {line.strip()}")

print("\nBUG-020 (will-change):")
for i, line in enumerate(lines):
    if "will-change" in line:
        print(f"{i + 1}: {line.strip()}")
