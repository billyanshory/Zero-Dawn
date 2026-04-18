with open('slb.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "with open(_probe_path, 'w') as f:" in line:
        print(f"Line {i+1}: {repr(line)}")
    if "_probe_path =" in line:
        print(f"Line {i+1}: {repr(line)}")
    if "f.write('ok')" in line:
        print(f"Line {i+1}: {repr(line)}")
