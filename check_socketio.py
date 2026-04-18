with open("app.py", "r") as f:
    if "message_queue=_redis_url" in f.read():
        print("SocketIO is correctly refactored.")
    else:
        print("SocketIO refactor failed.")
