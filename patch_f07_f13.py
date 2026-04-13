with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_send_web_push = """def send_web_push(subscription_info, message_body):
    if not VAPID_PRIVATE_KEY:
        app.logger.warning("VAPID_PRIVATE_KEY not configured, push skipped")
        return
    try:
        webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException:
        app.logger.error("Web Push delivery failed", exc_info=True)"""

new_send_web_push = """def send_web_push(subscription_info, message_body, subscription_id=None):
    if not VAPID_PRIVATE_KEY:
        app.logger.warning("VAPID_PRIVATE_KEY not configured, push skipped")
        return
    try:
        eventlet.tpool.execute(webpush, subscription_info=subscription_info, data=message_body, vapid_private_key=VAPID_PRIVATE_KEY, vapid_claims=VAPID_CLAIMS)
        if subscription_id:
            try:
                PushSubscription.query.filter_by(id=subscription_id).update({'last_used': datetime.datetime.now()})
                db.session.commit()
            except Exception:
                db.session.rollback()
    except WebPushException:
        app.logger.error("Web Push delivery failed", exc_info=True)"""

content = content.replace(old_send_web_push, new_send_web_push)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
