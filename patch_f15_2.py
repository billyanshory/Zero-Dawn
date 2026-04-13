with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "const medSocket = io();" in line:
        lines[i] = ""
    elif "medSocket.on('trigger_med_notification', function(data) {" in line:
        lines[i] = "        if (typeof socket !== 'undefined' && socket) { socket.on('trigger_med_notification', function(data) {\n"
    # Find matching closing brace and close the if block
    elif "        });" in line and "medication_name" in lines[i-4]: # very specific, check it
         pass

# Instead of passing, let's find the specific block
# It looks like:
# medSocket.on('trigger_med_notification', function(data) {
#    if ('serviceWorker' in navigator && 'PushManager' in window) {
#        navigator.serviceWorker.ready.then(function(registration) {
#            registration.showNotification(...)
#        });
#    }
# });
import re

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

content = content.replace("const medSocket = io();\n", "")
content = content.replace("medSocket.on('trigger_med_notification', function(data) {", "if (typeof socket !== 'undefined' && socket) { socket.on('trigger_med_notification', function(data) {")
content = content.replace("""                        requireInteraction: true
                    });
                });
            }
        });""", """                        requireInteraction: true
                    });
                });
            }
        }); }""")

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
