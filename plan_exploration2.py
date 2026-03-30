import re
with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

def print_section(start_line, num_lines):
    lines = content.split('\n')
    for i in range(start_line - 1, min(start_line - 1 + num_lines, len(lines))):
         print(f"{i+1}: {lines[i]}")

print_section(770, 40)
