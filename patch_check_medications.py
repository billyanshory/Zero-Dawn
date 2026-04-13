with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_check_medications = """def check_medications():
    with app.app_context():
        now = datetime.datetime.now()
        window_start = (now - datetime.timedelta(minutes=1)).time()
        window_end = (now + datetime.timedelta(minutes=1)).time()
        today = now.date()

        schedules = OrangTuaJadwal.query.filter(
            OrangTuaJadwal.schedule_time.between(window_start, window_end),
            OrangTuaJadwal.notified == False,
            db.or_(OrangTuaJadwal.notified_date == None, OrangTuaJadwal.notified_date < today)
        ).all()

        if not schedules:
            return

        subscriptions = PushSubscription.query.limit(500).all()

        schedules_data = []
        for sched in schedules:
            schedules_data.append({
                'time': sched.schedule_time.strftime('%H:%M') if sched.schedule_time else '',
                'medication_name': sched.medication_name
            })
            sched.notified = True
            sched.notified_date = today

        subscriptions_data = []
        for sub in subscriptions:
            try:
                subscriptions_data.append(json.loads(sub.subscription_info))
            except Exception as e:
                app.logger.error("Failed to parse subscription_info", exc_info=True)
                pass

        try:
            db.session.commit()
            threading.Thread(target=send_all_pushes, args=(schedules_data, subscriptions_data), daemon=True).start()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Medication check commit failed', exc_info=True)"""

new_check_medications = """def check_medications():
    with app.app_context():
        wita = pytz.timezone('Asia/Makassar')
        now = datetime.datetime.now(wita)
        window_start = (now - datetime.timedelta(minutes=1)).time()
        window_end = (now + datetime.timedelta(minutes=1)).time()
        today = now.date()

        if window_start <= window_end:
            time_filter = OrangTuaJadwal.schedule_time.between(window_start, window_end)
        else:
            time_filter = db.or_(OrangTuaJadwal.schedule_time >= window_start, OrangTuaJadwal.schedule_time <= window_end)

        schedules = OrangTuaJadwal.query.filter(
            time_filter,
            db.or_(OrangTuaJadwal.notified == False, OrangTuaJadwal.notified_date == None, OrangTuaJadwal.notified_date < today)
        ).all()

        if not schedules:
            return

        subscriptions = PushSubscription.query.order_by(PushSubscription.id.asc()).all()

        schedules_data = []
        for sched in schedules:
            schedules_data.append({
                'time': sched.schedule_time.strftime('%H:%M') if sched.schedule_time else '',
                'medication_name': sched.medication_name
            })
            sched.notified = True
            sched.notified_date = today

        subscriptions_data = []
        for sub in subscriptions:
            try:
                subscriptions_data.append((json.loads(sub.subscription_info), sub.id))
            except Exception as e:
                app.logger.error("Failed to parse subscription_info", exc_info=True)
                pass

        try:
            db.session.commit()
            for sched in schedules_data:
                socketio.emit('trigger_med_notification', {
                    'time': sched['time'],
                    'medication_name': sched['medication_name']
                })
            eventlet.spawn_n(send_all_pushes_only, schedules_data, subscriptions_data)
        except Exception as e:
            db.session.rollback()
            app.logger.error('Medication check commit failed', exc_info=True)"""

content = content.replace(old_check_medications, new_check_medications)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
