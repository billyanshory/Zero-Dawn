import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

constants_block = """
# NOTE: Template-side role/status literals in _HTML constants cannot reference these constants without a context_processor; tracked as residual risk for a follow-up cycle.
ROLE_ORANG_TUA = 'orang_tua'
ROLE_GURU = 'guru'
ROLE_KEPALA_SEKOLAH = 'kepala_sekolah'
STATUS_MENUNGGU = 'menunggu_verifikasi'
STATUS_DISETUJUI = 'disetujui'
STATUS_DITOLAK = 'ditolak'
ALL_ROLES = frozenset({ROLE_ORANG_TUA, ROLE_GURU, ROLE_KEPALA_SEKOLAH})
STAFF_ROLES = frozenset({ROLE_GURU, ROLE_KEPALA_SEKOLAH})
ALL_STATUSES = frozenset({STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK})
"""

# 1. Insert constants block
# Find db = SQLAlchemy(app)
db_decl = "db = SQLAlchemy(app)"
idx = content.find(db_decl)
if idx != -1:
    end_of_line = content.find("\n", idx)
    content = content[:end_of_line+1] + constants_block + content[end_of_line+1:]

# 2. Extract HTML templates (where we shouldn't replace)
# We will temporarily mask HTML constants to prevent replacements
html_pattern = re.compile(r"([A-Z_0-9]+_HTML\s*=\s*r?\"\"\"[\s\S]*?\"\"\")")

placeholders = {}
def replacer(match):
    idx = len(placeholders)
    key = f"__HTML_PLACEHOLDER_{idx}__"
    placeholders[key] = match.group(1)
    return key

content = html_pattern.sub(replacer, content)

# 3. Replace strings
# We must match exactly the string literals (including quotes)
# Examples: 'orang_tua' or "orang_tua"
content = re.sub(r"['\"]orang_tua['\"]", "ROLE_ORANG_TUA", content)

# 'guru' needs to be replaced in role contexts and db.Enum
# It might appear as 'guru' or "guru"
# We'll replace all literal 'guru' strings outside HTML.
# There might be some variable names, but re.sub matching exact quotes will only match literal strings.
content = re.sub(r"['\"]guru['\"]", "ROLE_GURU", content)

content = re.sub(r"['\"]kepala_sekolah['\"]", "ROLE_KEPALA_SEKOLAH", content)

content = re.sub(r"['\"]menunggu_verifikasi['\"]", "STATUS_MENUNGGU", content)
content = re.sub(r"['\"]disetujui['\"]", "STATUS_DISETUJUI", content)
content = re.sub(r"['\"]ditolak['\"]", "STATUS_DITOLAK", content)

# 4. Restore HTML templates
for key, val in placeholders.items():
    content = content.replace(key, val)

with open(fname, 'w') as f:
    f.write(content)
