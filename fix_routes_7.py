import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r'q = EmotionJournal\.query\s*if session\.get\(\'peran\'\) == \'orang_tua\' and session\.get\(\'anak_id\'\):\s*q = q\.filter_by\(anak_id=session\.get\(\'anak_id\'\)\)\.limit\(20\)\s*else:\s*q = q\.limit\(5\)\s*history = q\.order_by\(EmotionJournal\.date\.desc\(\)\)\.all\(\)',
r'''q = EmotionJournal.query
    if session.get('peran') == 'orang_tua' and session.get('anak_id'):
        history = q.filter_by(anak_id=session.get('anak_id')).order_by(EmotionJournal.date.desc()).limit(20).all()
    else:
        history = q.order_by(EmotionJournal.date.desc()).limit(5).all()''', content)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
