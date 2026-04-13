with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "r") as f:
    content = f.read()

old_code = "socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else [])"
new_code = """_cors_origins = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else '*'
_cors_origins = [o.strip() for o in _cors_origins if o.strip()] if isinstance(_cors_origins, list) else _cors_origins
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=_cors_origins)"""

content = content.replace(old_code, new_code)

with open("sekolah-luar-biasa-77 ( idcloudhost - Thirteenth Layer of Quality Control - Authorization & Access Control Consistency - v.76 - Opus 4.6 Ex. Think. ).py", "w") as f:
    f.write(content)
