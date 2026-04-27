import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    text = f.read()

# Fix the orphaned decorator by ensuring the function stays under it
# The problem happened because `def idul_adha_dashboard():` was replaced, but its decorator `@app.route('/idul-adha')` was left above the imports

bad_chunk = """@app.route('/idul-adha')

import csv
from io import StringIO
from flask import make_response

@app.route('/idul-adha/absen-panitia')"""

fixed_chunk = """
import csv
from io import StringIO
from flask import make_response

@app.route('/idul-adha/absen-panitia')"""

text = text.replace(bad_chunk, fixed_chunk)

# Now we need to put the @app.route('/idul-adha') back where it belongs, right above def idul_adha_dashboard():
target = "def idul_adha_dashboard():"
fixed_target = "@app.route('/idul-adha')\ndef idul_adha_dashboard():"

text = text.replace(target, fixed_target)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(text)
