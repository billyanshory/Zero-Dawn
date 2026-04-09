import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Tailwind CDN -> Tailwind CSS Link, remove tailwind.config
    content = re.sub(
        r'<script src="https://cdn\.tailwindcss\.com"></script>\s*<script>\s*tailwind\.config = \{.*?\};\s*</script>',
        r'<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3/dist/tailwind.min.css" rel="stylesheet">',
        content,
        flags=re.DOTALL
    )

    # In case there's another format of tailwind config:
    content = re.sub(
        r'<script src="https://cdn\.tailwindcss\.com"></script>',
        r'<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3/dist/tailwind.min.css" rel="stylesheet">',
        content
    )
    content = re.sub(
        r'<script>\s*tailwind\.config = \{.*?\};\s*</script>',
        r'',
        content,
        flags=re.DOTALL
    )

    # 2. Flask-Compress
    if 'from flask_compress import Compress' not in content:
        content = re.sub(
            r'(from flask import Flask.*?)(?=\n)',
            r'\1\nfrom flask_compress import Compress',
            content,
            count=1
        )
    if 'Compress(app)' not in content:
        content = re.sub(
            r'(app = Flask\(__name__\).*?)(?=\n)',
            r'\1\nCompress(app)',
            content,
            count=1
        )

    # 3. ramadhan_dashboard bug
    content = content.replace(
        'StudentPortfolio.query.limit(100).order_by(StudentPortfolio.created_at.desc()).all()',
        'StudentPortfolio.query.order_by(StudentPortfolio.created_at.desc()).limit(100).all()'
    )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
