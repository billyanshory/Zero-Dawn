with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

# Update const socket = io(); inside base template setup
# We need to be careful as there might be multiple 'const socket = io();'. We specifically want the one after `// BASE_LAYOUT_JS` around line 1096.

# Let's read by lines to be precise.
lines = content.split('\n')
for i, line in enumerate(lines):
    if "const socket = io();" in line and "globalAudioCtx" in lines[i+1]:
        lines[i] = line.replace("const socket = io();", "const socket = (typeof io !== 'undefined') ? io() : null;")

    if "socket.on('receive_frequency'" in line and "window.processFrequencyData(data);" in lines[i+1]:
        lines[i] = "        if (socket) { socket.on('receive_frequency', function(data) {"
        lines[i+1] = "            window.processFrequencyData(data);"
        lines[i+2] = "        }); }"

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write('\n'.join(lines))
