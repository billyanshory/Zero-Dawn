with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

# the replace didn't work previously because of loadJadwalTimeline();. Let's do it manually.

old_str = """            } else if (Notification.permission === "granted") {
                // Fallback standard notification
                new Notification("Waktunya Obat/Terapi!", {
                    body: data.medication_name + " pada jam " + data.time,
                    icon: "/static/logoslb.png"
                });
                loadJadwalTimeline();
            }
        });"""
new_str = """            } else if (Notification.permission === "granted") {
                // Fallback standard notification
                new Notification("Waktunya Obat/Terapi!", {
                    body: data.medication_name + " pada jam " + data.time,
                    icon: "/static/logoslb.png"
                });
                loadJadwalTimeline();
            }
        }); }"""

content = content.replace(old_str, new_str)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
