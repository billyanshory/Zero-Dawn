import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "def add(self, sid: str, device_id: str)" in lines[i]:
        # print the next 15 lines to see indentation
        for j in range(i-5, i+5):
            print(f"{j+1:4d}: {repr(lines[j])}")
        break
