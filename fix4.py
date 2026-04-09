import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Add missing indexes to KognitifBentukLog, KognitifEmosiLog, ReactionTimeLog
    # For ReactionTimeLog
    if "Index('idx_reaction_created', 'created_at')" not in content:
        content = content.replace(
            "class ReactionTimeLog(db.Model):\n    __tablename__ = 'reaction_time_log'",
            "class ReactionTimeLog(db.Model):\n    __tablename__ = 'reaction_time_log'\n    __table_args__ = (db.Index('idx_reaction_created', 'created_at'),)"
        )
        content = content.replace(
            "created_at = db.Column(db.DateTime, server_default=func.now())",
            "created_at = db.Column(db.DateTime, server_default=func.now(), index=True)"
        )

    # For KognitifEmosiLog
    if "Index('idx_kognitif_emosi_created', 'created_at')" not in content:
        content = content.replace(
            "class KognitifEmosiLog(db.Model):\n    __tablename__ = 'kognitif_emosi_log'",
            "class KognitifEmosiLog(db.Model):\n    __tablename__ = 'kognitif_emosi_log'\n    __table_args__ = (db.Index('idx_kognitif_emosi_created', 'created_at'),)"
        )

    # For KognitifBentukLog
    if "Index('idx_kognitif_bentuk_created', 'created_at')" not in content:
        content = content.replace(
            "class KognitifBentukLog(db.Model):\n    __tablename__ = 'kognitif_bentuk_log'",
            "class KognitifBentukLog(db.Model):\n    __tablename__ = 'kognitif_bentuk_log'\n    __table_args__ = (db.Index('idx_kognitif_bentuk_created', 'created_at'),)"
        )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
