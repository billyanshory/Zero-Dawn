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

grep_context(file_name, "def handle_ot_nutrisi")
grep_context(file_name, "def subscribe")
grep_context(file_name, "def save_burnout")
grep_context(file_name, "def slb_tunalaras")
grep_context(file_name, "def handle_connect")
grep_context(file_name, "def handle_disconnect")
grep_context(file_name, "def handle_set_frequency")
grep_context(file_name, "def send_web_push")
grep_context(file_name, "def therapy_log")
grep_context(file_name, "def generate_iep")
