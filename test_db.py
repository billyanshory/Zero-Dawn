import sys
import os

sys.path.append(".")
mod = __import__("klinik-delima-dalam-48 ( IdCloudHost - Tampilan Interface UI-UX - Tab Atas & Card Hard Digital )")

app = mod.app
db = mod.db
User = mod.User

with app.app_context():
    print(User.query.all()[0].to_dict())
    print(User.query.all()[1].to_dict())
