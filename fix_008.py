fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# I removed the global `import os` and `import pytz` then put them at the top.
# But wait, `eventlet.monkey_patch()` needs to be the FIRST executable line after `import eventlet`!!!
# Let's check the very top of the file:
# I put `import os\nimport pytz\n` at the VERY top, which breaks the eventlet rule.

# I need to restore the eventlet patch to the top.
lines = content.split('\n')
os_pytz = []
new_lines = []
for line in lines:
    if line == "import os" or line == "import pytz":
        os_pytz.append(line)
    else:
        new_lines.append(line)

content = "\n".join(new_lines)

# Now find where standard library imports are, e.g. after eventlet monkey_patch
idx = content.find("eventlet.monkey_patch()")
if idx != -1:
    end_line = content.find("\n", idx)
    content = content[:end_line+1] + "import os\nimport pytz\nfrom functools import wraps\n" + content[end_line+1:]

with open(fname, 'w') as f:
    f.write(content)
