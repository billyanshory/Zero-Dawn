import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

migration_note = """
# DEFERRED MIGRATION WORK: The following columns carry TODO markers indicating schema changes requiring Alembic or equivalent tooling: TantrumLog.duration_ms (nullable tightening), OrangTuaBuku.student_id (Integer + FK migration tracked as L1-020), OrangTuaTantrum.mood and .trigger (nullable tightening). See also the db.create_all() limitation note near end of file. Tracked under the Layer One remediation roadmap."""

# 1. Add block comment immediately above `class Siswa(db.Model):`
idx = content.find("class Siswa(db.Model):")
if idx != -1:
    content = content[:idx] + migration_note.lstrip() + "\n" + content[idx:]

# 2. Update TODO markers
def replace_todo(match):
    # If it already has it, skip
    if "see consolidated migration note above class Siswa" in match.group(0):
        return match.group(0)
    return match.group(0) + " (see consolidated migration note above class Siswa)"

content = re.sub(r"# TODO:.*?(?=\n)", replace_todo, content)

with open(fname, 'w') as f:
    f.write(content)
