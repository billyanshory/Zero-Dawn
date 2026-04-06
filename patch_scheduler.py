import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove global scheduler.start()
search_global_start = """scheduler = BackgroundScheduler()
scheduler.start()"""

replace_global_start = """scheduler = BackgroundScheduler()"""

if search_global_start in content:
    content = content.replace(search_global_start, replace_global_start)
else:
    print("global start not found")

# 2. Add start_scheduler_if_primary function and call it in app_context at bottom
search_bottom = """with app.app_context():
    try:
        prefetch_emoji_icons()
        db.create_all()"""

replace_bottom = """
import redis
def start_scheduler_if_primary():
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        if r.set('slb_scheduler_master', '1', nx=True, ex=3600):
            scheduler.start()
            app.logger.info("Started BackgroundScheduler in this worker.")
    except Exception as e:
        app.logger.error(f"Error acquiring scheduler lock: {e}")

with app.app_context():
    try:
        start_scheduler_if_primary()
        prefetch_emoji_icons()
        db.create_all()"""

if search_bottom in content:
    content = content.replace(search_bottom, replace_bottom)
else:
    print("bottom app context not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-005 Patched.")
