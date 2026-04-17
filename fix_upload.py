fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"

# I need to restore the ORIGINAL `upload_portfolio` and `upload_karya` logic
# Let's read it from the git repository before my commits.
import subprocess

original_file = subprocess.check_output(['git', 'show', 'HEAD:sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py']).decode('utf-8')

def extract_func(text, name):
    idx = text.find(f"def {name}(")
    end = text.find("def ", idx + 10)
    return text[idx:end]

orig_port = extract_func(original_file, "upload_portfolio")
orig_karya = extract_func(original_file, "upload_karya")

print("--- ORIGINAL upload_portfolio ---")
print(orig_port[:1500])
print("\n--- ORIGINAL upload_karya ---")
print(orig_karya[:1500])
