import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Audio tags without preload
    content = content.replace("<audio id=", '<audio preload="none" id=')
    content = content.replace("<audio src=", '<audio preload="none" src=')
    content = content.replace("const sndPop = new Audio(", "let sndPopUrl = ")

    # Needs socket.io conditional
    content = content.replace(
        '<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>',
        '{% if needs_socketio %}<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>{% endif %}'
    )

    # 10. PushSubscription unbounded
    content = content.replace(
        "subscriptions = PushSubscription.query.all()",
        "subscriptions = PushSubscription.query.yield_per(50)"
    )

    # 11. OrangTuaJadwal unbounded
    content = content.replace(
        "logs = q.order_by(OrangTuaJadwal.schedule_time.asc()).all()",
        "logs = q.order_by(OrangTuaJadwal.schedule_time.asc()).limit(100).all()"
    )

    # 12. prefetch_emoji_icons
    content = content.replace(
        "import urllib.request",
        "import requests\nimport urllib.request"
    )
    content = content.replace(
        "urllib.request.urlretrieve",
        "# urllib.request.urlretrieve"
    )
    content = content.replace(
        "def prefetch_emoji_icons():\n",
        "def prefetch_emoji_icons():\n    return\n"
    )

    # 13. get_settings invalidation
    content = content.replace(
        "cache.delete('settings')",
        "cache.delete_memoized(get_settings)"
    )

    # 14. db.create_all() wrapper
    content = content.replace(
        "db.create_all()",
        "if os.environ.get('FLASK_INIT_DB'):\n            db.create_all()"
    )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
