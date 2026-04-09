with open("sekolah_luar_biasa.py", "r") as f:
    content = f.read()

import re
content = re.sub(r"'connect_args':\s*\{\s*'connect_timeout':\s*10,\s*'options':\s*'-c\s*timezone=Asia/Makassar'\s*\}", "", content)

with open("sekolah_luar_biasa.py", "w") as f:
    f.write(content)
