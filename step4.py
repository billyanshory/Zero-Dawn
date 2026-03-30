with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Add Logging setup
logging_code = """
import logging
from logging.handlers import RotatingFileHandler

if not os.path.exists('error.log'):
    open('error.log', 'w').close()
error_handler = RotatingFileHandler('error.log', maxBytes=100000, backupCount=3)
error_handler.setLevel(logging.ERROR)
app.logger.addHandler(error_handler)
"""
content = content.replace("app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB Limit", "app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB Limit\n" + logging_code)

# 2. Inject to error handler
content = content.replace(
    "print(f\"Global Error Captured: {e}\")",
    "print(f\"Global Error Captured: {e}\")\n    app.logger.error(f\"Global Error Captured: {str(e)}\", exc_info=True)"
)

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
