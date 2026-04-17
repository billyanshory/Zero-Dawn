import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Add `flash` and `current_app` to `from flask import ...` at the top
content = re.sub(
    r"(from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string)",
    r"\1, flash, current_app",
    content
)

# Delete inline `from flask import flash` and `current_app`
content = re.sub(r"^[ \t]*from flask import flash[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*from flask import current_app[ \t]*\n", "", content, flags=re.MULTILINE)

# 2. Add `import io` to the top standard library imports
# Find a good spot, maybe after `import json`
content = content.replace("import json", "import io\nimport json", 1)

# Delete inline `import io as _io`
content = re.sub(r"^[ \t]*import io as _io[ \t]*\n", "", content, flags=re.MULTILINE)
# Replace `_io.BytesIO` with `io.BytesIO`
content = content.replace("_io.BytesIO", "io.BytesIO")

# 3. Hoist `from PIL import Image` to the top
# Find third-party imports, e.g., after `from flask_sqlalchemy`
content = content.replace("from flask_sqlalchemy import SQLAlchemy", "from flask_sqlalchemy import SQLAlchemy\nfrom PIL import Image")
# Delete inline
content = re.sub(r"^[ \t]*from PIL import Image[ \t]*\n", "", content, flags=re.MULTILINE)

# 4. Hoist `from datetime import datetime as dt_module`
# Next to `from datetime import time as dt_time`
content = content.replace("from datetime import time as dt_time", "from datetime import time as dt_time, datetime as dt_module")
content = re.sub(r"^[ \t]*from datetime import datetime as dt_module[ \t]*\n", "", content, flags=re.MULTILINE)

# 5. Hoist `from reportlab.platypus import KeepTogether`
content = content.replace(
    "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage",
    "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether"
)
content = re.sub(r"^[ \t]*from reportlab\.platypus import KeepTogether[ \t]*\n", "", content, flags=re.MULTILINE)

# 6. Hoist `import traceback` and `from pywebpush import webpush, WebPushException`
# We can add `import traceback` near `import sys` or `import os`
content = content.replace("import os\n", "import os\nimport traceback\n", 1)
# Add pywebpush near PIL or flask_sqlalchemy
content = content.replace("from PIL import Image", "from PIL import Image\nfrom pywebpush import webpush, WebPushException")
content = re.sub(r"^[ \t]*import traceback[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*from pywebpush import webpush, WebPushException[ \t]*\n", "", content, flags=re.MULTILINE)

# 7. Hoist `import urllib.parse` and merge `import urllib.request`
# Add `import urllib.parse\nimport urllib.request` near `import json`
content = content.replace("import json", "import urllib.parse\nimport urllib.request\nimport json", 1)
# Delete duplicates below
content = re.sub(r"^[ \t]*import urllib\.parse[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*import urllib\.request[ \t]*\n", "", content, flags=re.MULTILINE)
# Also there is a duplicate os and pytz mentioned at line 6779. Let's remove them globally if they are duplicated, but only inline ones.
# Find `def therapy_log()` or somewhere around that and just remove them.
content = re.sub(r"^[ \t]*import os[ \t]*\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^[ \t]*import pytz[ \t]*\n", "", content, flags=re.MULTILINE)
# BUT wait, the very top level `import os` and `import pytz` will be deleted by this!
# We must restore them at the top!
# Wait, actually we can just find them and restore them.
content = "import os\nimport pytz\n" + content

# 8. Hoist `from functools import wraps`
content = content.replace("import math\n", "import math\nfrom functools import wraps\n", 1)
content = re.sub(r"^[ \t]*from functools import wraps[ \t]*\n", "", content, flags=re.MULTILINE)

# Optional dependency note:
content = content.replace("try:\n    from flask_compress import Compress", "# Optional dependency: flask_compress. Failure is non-fatal; compression is disabled gracefully.\ntry:\n    from flask_compress import Compress")


with open(fname, 'w') as f:
    f.write(content)
