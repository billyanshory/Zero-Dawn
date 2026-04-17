import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

legacy_api_code = """@app.route('/api/kamus_nutrisi')
def api_kamus_nutrisi_legacy_redirect():
    return redirect(url_for('api_kamus_nutrisi'), code=301)"""

def replace_route(text, target):
    # Find the decorator and the def
    # @app.route('/api/kamus_nutrisi')
    # def api_kamus_nutrisi_underscore():
    # ...

    lines = text.split('\n')
    start = -1
    for i, line in enumerate(lines):
        if line.strip() == "@app.route('/api/kamus_nutrisi')":
            # check if next line is def api_kamus_nutrisi_underscore()
            if "def api_kamus_nutrisi_underscore" in lines[i+1]:
                start = i
                break

    if start == -1:
        return text

    i = start + 2
    while i < len(lines):
        if lines[i].strip() == "" or lines[i].startswith(" ") or lines[i].startswith("\t"):
            i += 1
        else:
            break

    end = i

    return "\n".join(lines[:start]) + "\n" + legacy_api_code + "\n" + "\n".join(lines[end:])

content = replace_route(content, "")

with open(fname, 'w') as f:
    f.write(content)
