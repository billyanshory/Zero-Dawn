import re

with open("app.py", "r") as f:
    content = f.read()

# RAMADHAN_DASHBOARD_HTML and IRMA_DASHBOARD_HTML open modal
# Ramadhan
content = re.sub(
    r"const open = '\{\{ open_modal \}\}';\s*if\(open && open !== 'None'\) openModal\(open\);",
    r"const open = {{ open_modal|tojson }};\n        if(open) openModal(open);",
    content
)

# IRMA open modal might have different indent
content = re.sub(
    r"const open = '\{\{ open_modal \}\}';\s*if\(open && open !== 'None'\) openModal\(open\);",
    r"const open = {{ open_modal|tojson }};\n            if(open) openModal(open);",
    content
)

# IDUL_ADHA pin
content = content.replace("const pin = '{{ shohibul.pin }}';", "const pin = {{ shohibul.pin|tojson }};")

with open("app.py", "w") as f:
    f.write(content)

print("Patch 3 applied.")
