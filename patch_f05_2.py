with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_start_scheduler = """def start_scheduler_if_primary():
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        if r.set('slb_scheduler_master', '1', nx=True, ex=3600):
            scheduler.start()
            app.logger.info("Started BackgroundScheduler in this worker.")
    except Exception as e:
        app.logger.error("Error acquiring scheduler lock", exc_info=True)"""

new_start_scheduler = """def start_scheduler_if_primary():
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        worker_id = str(uuid.uuid4())
        lock_key = 'slb_scheduler_master'
        if r.set(lock_key, worker_id, nx=True, ex=120):
            scheduler.start()
            app.logger.info("Started BackgroundScheduler in this worker.")

            def renew_lock():
                while True:
                    eventlet.sleep(60)
                    try:
                        current_owner = r.get(lock_key)
                        if current_owner and current_owner.decode() == worker_id:
                            r.expire(lock_key, 120)
                    except Exception:
                        pass

            eventlet.spawn(renew_lock)
    except Exception as e:
        app.logger.error("Error acquiring scheduler lock", exc_info=True)"""

content = content.replace(old_start_scheduler, new_start_scheduler)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
