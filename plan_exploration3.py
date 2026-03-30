with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    lines = f.readlines()

def grep_lines(pattern):
    for i, line in enumerate(lines):
        if pattern in line:
            print(f"{i+1}: {line.strip()}")

print("--- Routes ---")
grep_lines("@app.route('/dosen')")
grep_lines("@app.route('/mahasiswa')")
grep_lines("@app.route('/tu_dashboard')")

print("--- STYLES_HTML ---")
grep_lines("STYLES_HTML =")
