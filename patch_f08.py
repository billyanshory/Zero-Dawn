with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_job1 = "scheduler.add_job(id='Medication Check', func=check_medications, trigger='cron', minute='*')"
new_job1 = "scheduler.add_job(id='Medication Check', func=check_medications, trigger='cron', minute='*', max_instances=1, coalesce=True, misfire_grace_time=120)"

old_job2 = "scheduler.add_job(id='Cleanup Subscriptions', func=cleanup_push_subscriptions, trigger='cron', hour=3, minute=0)"
new_job2 = "scheduler.add_job(id='Cleanup Subscriptions', func=cleanup_push_subscriptions, trigger='cron', hour=3, minute=0, max_instances=1, coalesce=True, misfire_grace_time=3600)"

content = content.replace(old_job1, new_job1)
content = content.replace(old_job2, new_job2)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
