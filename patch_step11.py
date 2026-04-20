with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search_connect = """@socketio.on('connect')
def handle_connect() -> None:
    \"\"\"Handles SocketIO events for handle_connect.\"\"\"
    try:
        if not session.get('user_id'):
            return False"""

replace_connect = """@socketio.on('connect')
def handle_connect() -> None:
    \"\"\"Handles SocketIO events for handle_connect.\"\"\"
    try:
        if not session.get('user_id'):
            return False
        join_room(f"user_{session.get('user_id')}")"""

search_frequency = """        if mode == 'noise':
            if data.get('type') not in ['white', 'pink', 'brown']:
                return

        emit('receive_frequency', data, broadcast=True)
    except Exception:
        app.logger.error('SocketIO set_frequency handler failed', exc_info=True)"""

replace_frequency = """        if mode == 'noise':
            if data.get('type') not in ['white', 'pink', 'brown']:
                return

        room = session.get('room') or f"user_{session.get('user_id')}"
        emit('receive_frequency', data, room=room)
    except Exception:
        app.logger.error('SocketIO set_frequency handler failed', exc_info=True)"""

if search_connect in text and search_frequency in text:
    text = text.replace(search_connect, replace_connect)
    text = text.replace(search_frequency, replace_frequency)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
