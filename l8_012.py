import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

constants_block = """
THUMBNAIL_MAX_SIZE = (800, 800)  # Maximum pixel dimensions for uploaded image thumbnails
UPLOAD_MAX_BYTES = 5 * 1024 * 1024  # 5 MB cap on uploaded files
COMPRESSION_TARGET_BYTES = 500 * 1024  # Target size for JPEG compression in bytes
RATE_LIMIT_CALCULATOR = "30 per minute"
RATE_LIMIT_OT_API = "20 per minute"
RATE_LIMIT_UPLOAD = "10 per minute"
"""

# Find where to insert (after role constants block)
idx = content.find("ALL_STATUSES = frozenset({STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK})")
if idx != -1:
    end_line = content.find("\n", idx)
    content = content[:end_line+1] + constants_block + content[end_line+1:]

# Replace (800, 800) with THUMBNAIL_MAX_SIZE
content = content.replace("(800, 800)", "THUMBNAIL_MAX_SIZE")

# The upload_max_bytes might not be an exact literal but the instructions say to declare it. Let's look for `5 * 1024 * 1024`
content = content.replace("5 * 1024 * 1024", "UPLOAD_MAX_BYTES")

# Replace 500*1024 and 500 * 1024
content = content.replace("500*1024", "COMPRESSION_TARGET_BYTES")
content = content.replace("500 * 1024", "COMPRESSION_TARGET_BYTES")

# Replace decorators
content = content.replace('@limiter.limit("30 per minute")', '@limiter.limit(RATE_LIMIT_CALCULATOR)')
content = content.replace("@limiter.limit('30 per minute')", '@limiter.limit(RATE_LIMIT_CALCULATOR)')
content = content.replace('@limiter.limit("20 per minute")', '@limiter.limit(RATE_LIMIT_OT_API)')
content = content.replace("@limiter.limit('20 per minute')", '@limiter.limit(RATE_LIMIT_OT_API)')
content = content.replace('@limiter.limit("10 per minute")', '@limiter.limit(RATE_LIMIT_UPLOAD)')
content = content.replace("@limiter.limit('10 per minute')", '@limiter.limit(RATE_LIMIT_UPLOAD)')

with open(fname, 'w') as f:
    f.write(content)
