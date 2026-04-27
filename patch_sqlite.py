import re

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fallback mechanism for SQLite so we don't break MySQL but can use memory for tests.
# Find the exact SQLALCHEMY_DATABASE_URI line
old_line = "app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://alhijrahdelima_user:4lh1jr4hd3l1m5A!@localhost/alhijrahdelima'"
new_line = "app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql+pymysql://alhijrahdelima_user:4lh1jr4hd3l1m5A!@localhost/alhijrahdelima')"

content = content.replace(old_line, new_line)

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
