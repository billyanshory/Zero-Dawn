fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

content = content.replace("import io\nimport io\nimport io\n", "import io\n")
content = content.replace("from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, KeepTogether, KeepTogether", "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether")
content = content.replace("from sqlalchemy.exc import IntegrityError, OperationalError, OperationalError", "from sqlalchemy.exc import IntegrityError, OperationalError")
content = content.replace("from datetime import time as dt_time, datetime as dt_module, datetime as dt_module, datetime as dt_module", "from datetime import time as dt_time, datetime as dt_module")
content = content.replace("from datetime import time as dt_time, datetime as dt_module, datetime as dt_module", "from datetime import time as dt_time, datetime as dt_module")

if "from PIL import Image" not in content:
    idx = content.find("from flask_sqlalchemy import SQLAlchemy")
    content = content[:idx] + "from PIL import Image\n" + content[idx:]

if "from pywebpush import webpush, WebPushException" not in content:
    idx = content.find("from PIL import Image")
    content = content[:idx] + "from pywebpush import webpush, WebPushException\n" + content[idx:]

if "import traceback" not in content:
    idx = content.find("import os")
    content = content[:idx] + "import traceback\n" + content[idx:]

if "import urllib.parse\nimport urllib.request\n" not in content:
    idx = content.find("import json\n")
    content = content[:idx] + "import urllib.parse\nimport urllib.request\n" + content[idx:]

with open(fname, 'w') as f:
    f.write(content)
