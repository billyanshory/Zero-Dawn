file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove the extra """ that was added by mistake
content = re.sub(r'</script>\n\n"""\n\n"""\n\nRAMADHAN_DASHBOARD_HTML = """', '</script>\n\n"""\n\nRAMADHAN_DASHBOARD_HTML = """', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
