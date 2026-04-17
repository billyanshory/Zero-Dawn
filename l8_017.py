import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Insert TOC after the final import line.
# Let's find the last import line.
# `from reportlab.lib.pagesizes import A4` is a good marker, or just before `# --- CONFIGURATION ---`
toc_comment = """
# ============================================================
# TABLE OF CONTENTS
# ============================================================
# - Imports
# - App Configuration & Helper Functions
# - Database Models
# - Seed Data Function
# - STYLES_HTML Template
# - HOME_HTML Template
# - Home Page & Auth Routes
# - Calculator & Therapy Routes
# - RAMADHAN_DASHBOARD_HTML Template
# - SLB Disability Types HTML (TUNANETRA, TUNARUNGU, etc.)
# - ORANG_TUA_HTML Template
# - Parent API Routes
# - Push Notification Block
# - Gallery Upload Routes
# - Application Startup Block
# ============================================================
"""

idx = content.find("app = Flask(__name__)")
if idx != -1:
    # insert before the config block
    # backtrack to find the previous newline
    start_config = content.rfind("\n", 0, idx)
    content = content[:start_config+1] + toc_comment + "\n" + content[start_config+1:]

# 2. Add banners above _HTML template constant assignments
templates = [
    "STYLES_HTML", "HOME_HTML", "RAMADHAN_DASHBOARD_HTML",
    "TUNANETRA_HTML", "TUNARUNGU_HTML", "TUNAGRAHITA_HTML",
    "TUNADAKSA_HTML", "TUNALARAS_HTML", "TUNAGANDA_HTML",
    "ORANG_TUA_HTML", "ERROR_500_HTML" # wait, we will create ERROR_500_HTML later. Let's do it now if present or just the 10 mentioned.
]

for tmpl in templates:
    pattern = rf"^({tmpl}\s*=\s*r?\"\"\")"
    replacement = rf"# ============================================================\n# TEMPLATE: {tmpl}\n# CONSUMED BY: multiple route handlers\n# ============================================================\n\1"
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Banners for major route handler clusters
# We'll just add some basic ones
# "Home Page & Auth Routes" -> search for `def index():`
content = content.replace("def index():", "# ============================================================\n# ROUTE GROUP: Home Page & Auth Routes\n# ============================================================\ndef index():")

# "Calculator & Therapy Routes" -> search for `def bmi_calculator():`
content = content.replace("@app.route('/kalkulator')", "# ============================================================\n# ROUTE GROUP: Calculator & Therapy Routes\n# ============================================================\n@app.route('/kalkulator')")

# "Parent API Routes" -> search for `@app.route('/api/anak/<int:anak_id>')`
content = content.replace("@app.route('/api/anak/<int:anak_id>')", "# ============================================================\n# ROUTE GROUP: Parent API Routes\n# ============================================================\n@app.route('/api/anak/<int:anak_id>')")

# "Push Notification Block" -> search for `def subscribe_push():`
content = content.replace("@app.route('/subscribe', methods=['POST'])", "# ============================================================\n# ROUTE GROUP: Push Notification Block\n# ============================================================\n@app.route('/subscribe', methods=['POST'])")

# "Gallery Upload Routes" -> search for `def upload_portfolio(`
content = content.replace("def upload_portfolio(", "# ============================================================\n# ROUTE GROUP: Gallery Upload Routes\n# ============================================================\ndef upload_portfolio(")

# "Application Startup Block" -> search for `if __name__ == '__main__':`
content = content.replace("if __name__ == '__main__':", "# ============================================================\n# ROUTE GROUP: Application Startup Block\n# ============================================================\nif __name__ == '__main__':")

with open(fname, 'w') as f:
    f.write(content)
