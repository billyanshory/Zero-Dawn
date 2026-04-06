import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

models_to_check = ["AkunPengguna", "EpilepsiLog", "TantrumLog", "StudentPortfolio", "OrangTuaJadwal"]
for model in models_to_check:
    print(f"Checking {model}...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if f"class {model}(db.Model):" in line:
            for j in range(i, i+15):
                if 'index=True' in lines[j]:
                    print(f"  {lines[j].strip()}")
            break
