fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "if kind.extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:" in line:
        for j in range(i-5, i+5):
            print(f"{j+1:4d}: {repr(lines[j])}")
        break
