import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Also add composite index to the EmotionJournal model: Index('idx_emotion_journal_anak_date', 'anak_id', 'date')
    if "Index('idx_emotion_journal_anak_date'" not in content:
        # Let's find EmotionJournal
        if "class EmotionJournal(db.Model):\n    __tablename__ = 'emotion_journal'" in content:
            content = content.replace(
                "class EmotionJournal(db.Model):\n    __tablename__ = 'emotion_journal'",
                "class EmotionJournal(db.Model):\n    __tablename__ = 'emotion_journal'\n    __table_args__ = (db.Index('idx_emotion_journal_anak_date', 'anak_id', 'date'),)"
            )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
