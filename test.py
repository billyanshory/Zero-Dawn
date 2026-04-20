import re
with open("app_backup.py", "r") as f:
    text = f.read()

text = text.replace("if k in msg:", """if k in msg:""")
print(len(text))
