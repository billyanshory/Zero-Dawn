fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Ah, my script replaced the literal `(800, 800)` with `THUMBNAIL_MAX_SIZE` everywhere, INCLUDING in the declaration!
# So it became `THUMBNAIL_MAX_SIZE = THUMBNAIL_MAX_SIZE`!

content = content.replace("THUMBNAIL_MAX_SIZE = THUMBNAIL_MAX_SIZE", "THUMBNAIL_MAX_SIZE = (800, 800)")
content = content.replace("UPLOAD_MAX_BYTES = UPLOAD_MAX_BYTES", "UPLOAD_MAX_BYTES = 5 * 1024 * 1024")
content = content.replace("COMPRESSION_TARGET_BYTES = COMPRESSION_TARGET_BYTES", "COMPRESSION_TARGET_BYTES = 500 * 1024")

with open(fname, 'w') as f:
    f.write(content)
