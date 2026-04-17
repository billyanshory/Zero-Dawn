fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Add wraps to the top
if "from functools import wraps" not in content[:500]:
    # Insert it right after eventlet
    idx = content.find("eventlet.monkey_patch()")
    if idx != -1:
        end = content.find("\n", idx)
        content = content[:end+1] + "from functools import wraps\n" + content[end+1:]

with open(fname, 'w') as f:
    f.write(content)
