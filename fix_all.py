import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# I need to do these transformations correctly, avoiding the pitfalls found in the review.
# The review found 4 specific regressions:
# 1. Broken HTML forms (string replacement caught non-python strings).
# 2. Hallucinated ORM models in upload_portfolio and upload_karya.
# 3. Broken route signature in upload_portfolio (missing param in route decorator or vice-versa).
# 4. ERROR_500_HTML constant misplaced resulting in NameError.

# Let's perform the transformations carefully step by step from the original file.

# L8-010: Remove DALIL_DATA
idx_dalil = content.find("# --- DATA SUMBER HUKUM (DALIL) ---")
if idx_dalil != -1:
    end_dalil = content.find("}", idx_dalil) + 1
    # also remove trailing newlines
    while end_dalil < len(content) and content[end_dalil] in ['\n', ' ']:
        end_dalil += 1
    content = content[:idx_dalil] + content[end_dalil:]

# L8-001: Role and Status Constants
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
idx_db = content.find("db = SQLAlchemy(app)")
if idx_db != -1:
    end_db = content.find("\n", idx_db)
    content = content[:end_db+1] + constants_block + content[end_db+1:]

# Mask HTML
html_pattern = re.compile(r"([A-Z_0-9]+_HTML\s*=\s*r?\"\"\"[\s\S]*?\"\"\")")
placeholders = {}
def replacer(match):
    key = f"__HTML_PLACEHOLDER_{len(placeholders)}__"
    placeholders[key] = match.group(1)
    return key
content = html_pattern.sub(replacer, content)

# Now we only replace exactly `'orang_tua'` etc. We will only match Python string literals, not random text.
def replace_literal(text, lit, replacement):
    # Match 'lit' or "lit", ensuring it's not part of a larger word
    text = re.sub(rf"'{lit}'", replacement, text)
    text = re.sub(rf'"{lit}"', replacement, text)
    return text

content = replace_literal(content, "orang_tua", "ROLE_ORANG_TUA")
content = replace_literal(content, "guru", "ROLE_GURU")
content = replace_literal(content, "kepala_sekolah", "ROLE_KEPALA_SEKOLAH")
content = replace_literal(content, "menunggu_verifikasi", "STATUS_MENUNGGU")
content = replace_literal(content, "disetujui", "STATUS_DISETUJUI")
content = replace_literal(content, "ditolak", "STATUS_DITOLAK")

# Restore HTML
for key, val in placeholders.items():
    content = content.replace(key, val)

# L8-002: Refactor Authorization Guards
def fix_guards(text):
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if "session.get('peran') not in" in line and "def require_auth" not in line and "not in roles:" not in line:
            match = re.search(r"not in \[(.*?)\]", line)
            if not match:
                combined = line + (lines[i+1] if i+1 < len(lines) else "")
                match = re.search(r"not in \[(.*?)\]", combined)
                if not match:
                    i += 1; continue

            roles_str = match.group(1)
            if "ROLE_ORANG_TUA" in roles_str and "ROLE_GURU" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str:
                decorator = "@require_auth(roles=ALL_ROLES)"
            elif "ROLE_GURU" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str and "ROLE_ORANG_TUA" not in roles_str:
                decorator = "@require_auth(roles=STAFF_ROLES)"
            elif "ROLE_ORANG_TUA" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str and "ROLE_GURU" not in roles_str:
                decorator = "@require_auth(roles={ROLE_ORANG_TUA, ROLE_KEPALA_SEKOLAH})"
            else:
                decorator = f"@require_auth(roles={{{roles_str}}})"

            j = i
            while j >= 0 and not lines[j].strip().startswith("def "):
                j -= 1
            if j >= 0:
                lines.insert(j, " " * (len(lines[j]) - len(lines[j].lstrip())) + decorator)
                i += 1; j += 1
                base_indent = len(lines[i]) - len(lines[i].lstrip())
                del lines[i]
                while i < len(lines) and (len(lines[i]) - len(lines[i].lstrip()) > base_indent or lines[i].strip() == ""):
                    if len(lines[i].strip()) > 0 and len(lines[i]) - len(lines[i].lstrip()) <= base_indent:
                        break
                    del lines[i]
                continue
        i += 1
    return "\n".join(lines)

content = fix_guards(content)

# L8-008 & 009: Hoist Imports
content = re.sub(
    r"(from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string)",
    r"\1, flash, current_app", content
)
content = re.sub(r"^[ \t]*from flask import flash[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*from flask import current_app[ \t]*\n", "", content, flags=re.MULTILINE)

# io
idx_json = content.find("import json\n")
if idx_json != -1: content = content[:idx_json] + "import io\n" + content[idx_json:]
content = re.sub(r"^[ \t]*import io as _io[ \t]*\n", "", content, flags=re.MULTILINE)
content = content.replace("_io.BytesIO", "io.BytesIO")

# PIL
idx_sql = content.find("from flask_sqlalchemy import SQLAlchemy\n")
if idx_sql != -1: content = content[:idx_sql+len("from flask_sqlalchemy import SQLAlchemy\n")] + "from PIL import Image\n" + content[idx_sql+len("from flask_sqlalchemy import SQLAlchemy\n"):]
content = re.sub(r"^[ \t]*from PIL import Image[ \t]*\n", "", content, flags=re.MULTILINE)

# datetime
content = content.replace("from datetime import time as dt_time", "from datetime import time as dt_time, datetime as dt_module")
content = re.sub(r"^[ \t]*from datetime import datetime as dt_module[ \t]*\n", "", content, flags=re.MULTILINE)

# reportlab
content = content.replace(
    "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage",
    "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether"
)
content = re.sub(r"^[ \t]*from reportlab\.platypus import KeepTogether[ \t]*\n", "", content, flags=re.MULTILINE)

# traceback & pywebpush
idx_os = content.find("import os\n")
if idx_os != -1: content = content[:idx_os+len("import os\n")] + "import traceback\n" + content[idx_os+len("import os\n"):]
idx_pil = content.find("from PIL import Image\n")
if idx_pil != -1: content = content[:idx_pil+len("from PIL import Image\n")] + "from pywebpush import webpush, WebPushException\n" + content[idx_pil+len("from PIL import Image\n"):]
content = re.sub(r"^[ \t]*import traceback[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*from pywebpush import webpush, WebPushException[ \t]*\n", "", content, flags=re.MULTILINE)

# urllib
idx_io = content.find("import io\n")
if idx_io != -1: content = content[:idx_io] + "import urllib.parse\nimport urllib.request\n" + content[idx_io:]
content = re.sub(r"^[ \t]*import urllib\.parse[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*import urllib\.request[ \t]*\n", "", content, flags=re.MULTILINE)

# remove duplicate os and pytz (only lower down, keep top)
# Actually, it's safer to just remove them from inside therapy_log
therapy_log_idx = content.find("def therapy_log(")
if therapy_log_idx != -1:
    end = content.find("def ", therapy_log_idx + 10)
    body = content[therapy_log_idx:end]
    body = body.replace("    import os\n", "")
    body = body.replace("    import pytz\n", "")
    content = content[:therapy_log_idx] + body + content[end:]

# functools
idx_math = content.find("import math\n")
if idx_math != -1: content = content[:idx_math] + "from functools import wraps\n" + content[idx_math:]
content = re.sub(r"^[ \t]*from functools import wraps[ \t]*\n", "", content, flags=re.MULTILINE)

# flask_compress comment
content = content.replace("try:\n    from flask_compress import Compress", "# Optional dependency: flask_compress. Failure is non-fatal; compression is disabled gracefully.\ntry:\n    from flask_compress import Compress")


# L8-003: Extract Upload Helper
# The review said I completely hallucinated the DB logic.
# We need to look at the ORIGINAL upload_portfolio and upload_karya functions to see exactly what they do,
# then ONLY replace the file/image processing part with `_save_uploaded_media`.

# Let's save content so far and then carefully edit those two functions.
with open(fname, 'w') as f:
    f.write(content)
