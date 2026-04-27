import re

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Only apply engine options for mysql
old_engine = "app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 100, 'max_overflow': 200, 'pool_recycle': 280}"
new_engine = "if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:\n    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 100, 'max_overflow': 200, 'pool_recycle': 280}"

content = content.replace(old_engine, new_engine)

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
