import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "class _ConnectedClientsHolder" in lines[i]:
        # print the next 15 lines to see indentation
        for j in range(i, i+15):
            print(f"{j+1:4d}: {repr(lines[j])}")
        break
