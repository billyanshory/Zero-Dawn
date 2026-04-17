import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Let's check validator_approve and validator_reject specifically
def check_func(name):
    idx = content.find(f"def {name}(")
    if idx == -1:
        print(f"{name} not found")
        return
    end = content.find("def ", idx + 10)
    func_body = content[idx:end]
    print(f"--- {name} ---")
    if "except IntegrityError" in func_body:
        print("IntegrityError found")
    else:
        print("IntegrityError MISSING")

check_func("validator_approve")
check_func("validator_reject")
