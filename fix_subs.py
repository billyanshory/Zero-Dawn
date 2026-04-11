import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """def cleanup_push_subscriptions():
    with app.app_context():
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        PushSubscription.query.filter(PushSubscription.last_used < thirty_days_ago).delete()
        db.session.commit()

scheduler.add_job(id='Cleanup Subscriptions', func=cleanup_push_subscriptions, trigger='cron', hour=3, minute=0)"""

replacement = """def cleanup_push_subscriptions():
    with app.app_context():
        try:
            thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            PushSubscription.query.filter(PushSubscription.last_used < thirty_days_ago).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Subscription cleanup failed', exc_info=True)

scheduler.add_job(id='Cleanup Subscriptions', func=cleanup_push_subscriptions, trigger='cron', hour=3, minute=0)"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
