with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_send_all_pushes = """def send_all_pushes(schedules_data, subscriptions_data):
    with app.app_context():
        for sched in schedules_data:
            socketio.emit('trigger_med_notification', {
                'time': sched['time'],
                'medication_name': sched['medication_name']
            })
            for sub in subscriptions_data:
                try:
                    sub_info = sub
                    send_web_push(sub_info, f"Waktunya Obat/Terapi: {sched['medication_name']} pada jam {sched['time']}")
                except Exception:
                    app.logger.error('Push notification delivery failed', exc_info=True)"""

new_send_all_pushes = """def send_all_pushes_only(schedules_data, subscriptions_data):
    with app.app_context():
        for sched in schedules_data:
            for sub_info, sub_id in subscriptions_data:
                try:
                    send_web_push(sub_info, f"Waktunya Obat/Terapi: {sched['medication_name']} pada jam {sched['time']}", subscription_id=sub_id)
                except Exception:
                    app.logger.error('Push notification delivery failed', exc_info=True)"""

content = content.replace(old_send_all_pushes, new_send_all_pushes)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
