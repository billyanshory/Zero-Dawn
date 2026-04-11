import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """                pass

        db.session.commit()
        threading.Thread(target=send_all_pushes, args=(schedules_data, subscriptions_data), daemon=True).start()"""

replacement = """                pass

        try:
            db.session.commit()
            threading.Thread(target=send_all_pushes, args=(schedules_data, subscriptions_data), daemon=True).start()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Medication check commit failed', exc_info=True)
            return"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
