import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# For local testing without Redis, fallback to memory
content = content.replace("storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379/0')", "storage_uri=os.getenv('REDIS_URL', 'memory://')")

# Also for cache
content = content.replace("'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0')", "'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0') if os.getenv('REDIS_URL') else None")
content = content.replace("'CACHE_TYPE': 'RedisCache',", "'CACHE_TYPE': 'RedisCache' if os.getenv('REDIS_URL') else 'SimpleCache',")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
