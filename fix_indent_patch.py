with open('slb.py', 'r') as f:
    content = f.read()

content = content.replace(
    "        _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')\n    with open(_probe_path, 'w') as f:",
    "    _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')\n    with open(_probe_path, 'w') as f:"
)

with open('slb.py', 'w') as f:
    f.write(content)
