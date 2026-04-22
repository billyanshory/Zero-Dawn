import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

with open(filename, "r") as f:
    content = f.read()

# Replace int(request.form['key']) with int(request.form.get('key', 0))
content = re.sub(r"int\(\s*request\.form\['([^']+)'\]\s*\)", r"int(request.form.get('\1', 0))", content)

# Replace request.form['key'] with request.form.get('key', '')
content = re.sub(r"request\.form\['([^']+)'\]", r"request.form.get('\1', '')", content)

# Check for session reads (excluding assignments)
# Look for session['key'] not followed by =
content = re.sub(r"session\['([^']+)'\](?!\s*=)", r"session.get('\1', None)", content)

with open(filename, "w") as f:
    f.write(content)
