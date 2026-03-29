import re

file_path = "kampus-stie-samarinda-14 ( idcloudhost - bug fatal - pmb digital, publikasi informasi, tracer study ).py"
with open(file_path, "r") as f:
    code = f.read()

# Make sure imports are safe
if "\nimport io" in code and "from reportlab.pdfgen import canvas" not in code[:1000]:
    code = code.replace("import io", "import io\nfrom reportlab.pdfgen import canvas")

with open(file_path, "w") as f:
    f.write(code)
