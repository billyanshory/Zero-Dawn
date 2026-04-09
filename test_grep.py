with open("sekolah_luar_biasa.py", "r") as f:
    lines = f.readlines()

def print_context(func_name, before=2, after=15):
    for i, line in enumerate(lines):
        if func_name in line and "def " in line:
            print(f"--- {func_name} (Line {i+1}) ---")
            for j in range(max(0, i - before), min(len(lines), i + after)):
                print(f"{j+1}: {lines[j]}", end="")
            print()
            break

print_context("def update_profil_medis(")
print_context("def validator_approve(")
print_context("def validator_reject(")
