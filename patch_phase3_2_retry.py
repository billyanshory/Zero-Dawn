with open("app.py", "r") as f:
    content = f.read()

imports_patch = """import signal as _signal
import atexit as _atexit"""

if "import signal as _signal" not in content:
    content = content.replace("import os", "import os\n" + imports_patch)

# Find where to place the graceful shutdown logic
shutdown_code = """def _graceful_shutdown(signum=None, frame=None):
    app.logger.info("Graceful shutdown requested (signal=%s)", signum)

    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            app.logger.info("Scheduler shut down successfully.")
    except Exception:
        app.logger.warning("Failed to shut down scheduler.", exc_info=True)

    try:
        _redis_url = os.getenv('REDIS_URL')
        if _redis_url:
            r = redis.from_url(_redis_url, socket_timeout=2)
            r.delete("slb_scheduler_master")
            app.logger.info("Redis scheduler lock released.")
    except Exception:
        app.logger.warning("Failed to release Redis lock.", exc_info=True)

    try:
        db.session.remove()
        db.engine.dispose()
        app.logger.info("Database connection pool drained.")
    except Exception:
        app.logger.warning("Failed to drain database connections.", exc_info=True)

    try:
        for h in app.logger.handlers:
            h.flush()
    except Exception:
        pass

_signal.signal(_signal.SIGTERM, _graceful_shutdown)
_signal.signal(_signal.SIGINT, _graceful_shutdown)
_atexit.register(_graceful_shutdown)

with app.app_context():"""

# It looks like the string `with app.app_context():` might have existed in multiple places in the earlier faulty patch. Let's do a strict count and replace only the last one.
parts = content.rsplit("with app.app_context():", 1)
if len(parts) == 2:
    content = parts[0] + shutdown_code + parts[1]

with open("app.py", "w") as f:
    f.write(content)
