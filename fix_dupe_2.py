fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Let's remove the second occurrence.
idx1 = content.find("def _save_uploaded_media")
idx2 = content.find("def _save_uploaded_media", idx1 + 10)

if idx2 != -1:
    # Find the start of the class UploadValidationError before idx2
    class_idx = content.rfind("class UploadValidationError", idx1 + 10, idx2)
    end_idx = content.find("return filename", idx2) + len("return filename") + 1
    # also remove the trailing newline
    content = content[:class_idx] + content[end_idx:]

with open(fname, 'w') as f:
    f.write(content)
