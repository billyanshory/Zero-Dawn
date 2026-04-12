import sys

def grep_context(filename, search_text, context=5):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if search_text in line:
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            print(f"--- Found '{search_text}' at line {i+1} ---")
            for j in range(start, end):
                prefix = "*" if j == i else " "
                print(f"{j+1:4d}{prefix} {lines[j].rstrip()}")
            print("-" * 40)

file_name = "slb.py"

grep_context(file_name, "handler.setLevel(logging.ERROR)")
grep_context(file_name, "logging.error(f\"Terjadi kesalahan: {str(e)}\", exc_info=True)")
grep_context(file_name, "def send_all_pushes")
grep_context(file_name, "def get_list_siswa_cached")
grep_context(file_name, "def save_ot_buku")
grep_context(file_name, "def delete_ot_jadwal")
