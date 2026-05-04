import re

with open("app.py", "r") as f:
    content = f.read()

content = content.replace("@app.route('/fitur_masjid')", "@app.route('/fitur-masjid')")

with open("app.py", "w") as f:
    f.write(content)
