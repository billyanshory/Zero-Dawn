import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r"app\.config\['SQLALCHEMY_ENGINE_OPTIONS'\] = \{.*?\}",
r'''if os.getenv('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 20,
        'pool_pre_ping': True
    }''', content, flags=re.DOTALL)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
