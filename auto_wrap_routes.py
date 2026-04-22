import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    lines = f.readlines()

def wrap_function(func_name, lines):
    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith(f"def {func_name}("):
            start_idx = i
            break

    if start_idx == -1: return lines

    # Find end of function
    end_idx = start_idx + 1
    while end_idx < len(lines) and (lines[end_idx].startswith(" ") or lines[end_idx].strip() == ""):
        end_idx += 1

    func_lines = lines[start_idx+1:end_idx]

    # We will wrap everything inside the function in a try...except
    # But wait, we need to return something in the except block.
    # It's better to just do this with manual replace_with_git_merge_diff but with correct searches.
    return lines
