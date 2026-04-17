fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# I declared the constants too low! `_compress_image_to_bytes` is defined earlier than `ALL_STATUSES`.
# Let's move the new constants to the very top, just below the `import` statements or near `ALL_STATUSES` and move `_compress_image_to_bytes` below them if needed, OR just move the constants block higher.
# Wait, `ALL_STATUSES` is defined at line 192 (after SQLAlchemy). But `_compress_image_to_bytes` is defined at line 48!

# Let's move ALL the constants (`ROLE_*`, `STATUS_*`, `ALL_ROLES`, etc AND the new ones) above `_compress_image_to_bytes`.
# Wait, `ROLE_*` constants depend on `frozenset` which is built-in.
# I'll just hoist the `COMPRESSION_TARGET_BYTES`, `UPLOAD_MAX_BYTES`, `THUMBNAIL_MAX_SIZE` etc. to right before `_compress_image_to_bytes`.

lines = content.split('\n')
start = -1
for i, line in enumerate(lines):
    if line.startswith("THUMBNAIL_MAX_SIZE ="):
        start = i
        break

if start != -1:
    block = lines[start:start+6]
    lines = lines[:start] + lines[start+6:]

    # find `def _compress_image_to_bytes`
    target = -1
    for i, line in enumerate(lines):
        if line.startswith("def _compress_image_to_bytes"):
            target = i
            break

    lines = lines[:target] + block + lines[target:]

    with open(fname, 'w') as f:
        f.write("\n".join(lines))
