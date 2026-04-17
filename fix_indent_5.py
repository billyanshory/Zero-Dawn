import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# I see what happened. `_save_uploaded_media` got mangled when I removed the duplicate. Let's completely recreate it correctly.

def recreate_helper():
    global content

    # Remove any stray remnants of `UploadValidationError` or `_save_uploaded_media`
    # Also clean up the random `if kind.extension not in ...` lying around.

    # We will search for ALL_STATUSES and insert the full block, and try to remove any orphaned code below it.
    idx = content.find("ALL_STATUSES = frozenset({STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK})")

    if idx != -1:
        end_idx = content.find("\n", idx)

        # We need to find the start of the next legit class/def
        next_db_model = content.find("class ", end_idx)

        # remove everything between end_idx and next_db_model except blank lines if it looks like broken helper code.
        # Actually it's safer to just regex remove the broken code.
        broken_code_pattern = re.compile(r"^[ \t]*if kind\.extension not in \['jpg', 'jpeg', 'png', 'webp', 'gif'\]:[\s\S]*?raise UploadValidationError\(\"Gagal memproses gambar\.\"\)\n", re.MULTILINE)
        content = broken_code_pattern.sub("", content)

        # Remove the previous class UploadValidationError if it exists
        content = re.sub(r"class UploadValidationError\(Exception\):\n[ \t]*pass\n\n", "", content)

        # Remove any existing `def _save_uploaded_media`
        content = re.sub(r"def _save_uploaded_media.*?\n(?=def |class |@|\n\n\n|\n[A-Z_]+ = )", "", content, flags=re.DOTALL)

        helper_code = """
class UploadValidationError(Exception):
    pass

def _save_uploaded_media(file, upload_folder: str, video_extensions: frozenset[str] = frozenset({'mp4'})) -> str:
    \"\"\"Saves and processes an uploaded media file.\"\"\"
    if not file or file.filename == '':
        raise UploadValidationError("File tidak valid atau kosong.")
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    file_bytes = file.read()
    file.seek(0)

    kind = filetype.guess(file_bytes)
    if not kind:
        if ext == 'svg':
            raise UploadValidationError("File SVG tidak diperbolehkan demi keamanan.")
        raise UploadValidationError("Tipe file tidak dikenali.")

    if kind.extension in video_extensions:
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
        return filename

    if kind.extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise UploadValidationError("Format file tidak didukung.")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(THUMBNAIL_MAX_SIZE)
        compressed_bytes = eventlet.tpool.execute(_compress_image_to_bytes, img, COMPRESSION_TARGET_BYTES)
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(compressed_bytes)
        return filename
    except Exception as e:
        raise UploadValidationError("Gagal memproses gambar.")
"""

        # insert it again
        idx2 = content.find("ALL_STATUSES = frozenset({STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK})")
        if idx2 != -1:
            end2 = content.find("\n", idx2)
            content = content[:end2+1] + "\n" + helper_code + "\n" + content[end2+1:]

recreate_helper()

with open(fname, 'w') as f:
    f.write(content)
