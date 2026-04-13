with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

in_handle_connect = False
for i, line in enumerate(lines):
    if "def handle_connect():" in line:
        in_handle_connect = True
    if in_handle_connect and "except Exception:" in line:
        # Assuming the next line is the logger error.
        # Check next few lines to find it
        if "app.logger.error('SocketIO connect handler failed', exc_info=True)" in lines[i+1]:
            lines.insert(i+2, "        return False\n")
            break

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.writelines(lines)
