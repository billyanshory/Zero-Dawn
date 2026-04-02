import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

import_search = "from sqlalchemy import func, text"
import_replace = "from sqlalchemy import func, text\nfrom sqlalchemy.exc import IntegrityError"

code = code.replace(import_search, import_replace)

presensi_search = "except db.exc.IntegrityError:"
presensi_replace = "except IntegrityError:"

code = code.replace(presensi_search, presensi_replace)

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'w') as f:
    f.write(code)
