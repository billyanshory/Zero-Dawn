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

grep_context(file_name, "def validator_approve")
grep_context(file_name, "def validator_reject")
grep_context(file_name, "def get_tantrum_data")
grep_context(file_name, "def get_ot_chart_data")
grep_context(file_name, "def check_burnout")
grep_context(file_name, "def api_tunalaras_guru_monitor")
grep_context(file_name, "def prefetch_emoji_icons")
grep_context(file_name, "def seed_slb_data")
grep_context(file_name, "def start_scheduler_if_primary")
grep_context(file_name, "def login")
