import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

def replace_func_def(name, new_def, docstring):
    global content
    idx = content.find(f"def {name}")
    if idx == -1: return
    # Find end of definition line (the colon)
    # Be careful with multi-line definitions, let's assume they are single line for these helpers
    end_idx = content.find(":", idx)

    # insert docstring after the line
    next_line_idx = content.find("\n", end_idx)

    # Check if it already has docstring
    if '"""' not in content[next_line_idx:next_line_idx+20]:
        indent = "\n    "
        content = content[:next_line_idx] + indent + f'"""{docstring}"""' + content[next_line_idx:]

    # Replace definition
    content = content[:idx] + new_def + content[end_idx:]

# Let's do replacements safely
content = content.replace(
    "def validate_str(value, max_len=500):",
    "def validate_str(value: object, max_len: int = 500) -> str | None:\n    \"\"\"Validates and truncates a string input to a maximum length.\"\"\""
)

content = content.replace(
    "def _compress_image_to_bytes(img, max_bytes=COMPRESSION_TARGET_BYTES):",
    "def _compress_image_to_bytes(img: 'Image.Image', max_bytes: int = COMPRESSION_TARGET_BYTES) -> bytes:\n    \"\"\"Iteratively compresses a PIL Image to fit within max_bytes limit.\"\"\""
)

content = content.replace(
    "def cached_render(template_name, template_string, **context):",
    "def cached_render(template_name: str, template_string: str, **context: object) -> str:\n    \"\"\"Renders a Jinja template string with caching support.\"\"\""
)

content = content.replace(
    "def is_safe_redirect(url):",
    "def is_safe_redirect(url: str) -> bool:\n    \"\"\"Validates if a redirect URL is safe to follow (same host/relative).\"\"\""
)

content = content.replace(
    "def allowed_file(filename):",
    "def allowed_file(filename: str) -> bool:\n    \"\"\"Checks if a filename has an allowed extension.\"\"\""
)

content = content.replace(
    "def get_settings():",
    "def get_settings() -> dict[str, str]:\n    \"\"\"Fetches and caches application settings from the database.\"\"\""
)

content = content.replace(
    "def get_list_siswa_cached():",
    "def get_list_siswa_cached() -> list[dict[str, object]]:\n    \"\"\"Fetches and caches a lightweight list of students.\"\"\""
)

content = content.replace(
    "def invalidate_settings_cache():",
    "def invalidate_settings_cache() -> None:\n    \"\"\"Invalidates the manual application settings cache.\"\"\""
)

content = content.replace(
    "def seed_slb_data():",
    "def seed_slb_data() -> None:\n    \"\"\"Seeds the database with essential SLB data if empty.\"\"\""
)

content = content.replace(
    "def _save_uploaded_media(file, upload_folder, video_extensions=frozenset({'mp4'})):",
    "def _save_uploaded_media(file, upload_folder: str, video_extensions: frozenset[str] = frozenset({'mp4'})) -> str:\n    \"\"\"Saves and processes an uploaded media file.\"\"\""
)

with open(fname, 'w') as f:
    f.write(content)
