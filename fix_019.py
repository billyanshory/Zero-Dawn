fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

start = content.find("def seed_slb_data():")
if start != -1:
    end = content.find("def ", start + 10)
    func_body = content[start:end]
    print(func_body[:500])
