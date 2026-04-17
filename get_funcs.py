fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

def print_func(name):
    idx = content.find(f"def {name}")
    if idx != -1:
        end = content.find("def ", idx + 10)
        print(f"--- {name} ---")
        print(content[idx:end][:1500])

print_func("upload_portfolio")
print_func("upload_karya")
