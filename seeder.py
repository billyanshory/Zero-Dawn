import sqlite3
from werkzeug.security import generate_password_hash
import json

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create tables if not exist (minimal)
c.execute('''CREATE TABLE IF NOT EXISTS academy_users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, related_id TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS academy_students (id TEXT PRIMARY KEY, name TEXT, dob TEXT, category TEXT, position TEXT, guardian TEXT, guardian_wa TEXT, photo_path TEXT, user_id TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS finance_bills (id TEXT PRIMARY KEY, student_id TEXT, month TEXT, amount INTEGER, status TEXT DEFAULT 'unpaid', proof_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS academy_attendance (id TEXT PRIMARY KEY, date TEXT, student_id TEXT, status TEXT, coach_id TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS academy_evaluations (id TEXT PRIMARY KEY, month TEXT, student_id TEXT, coach_id TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

# Seed Student
pwd = generate_password_hash('pass123')
c.execute("INSERT OR REPLACE INTO academy_users (username, password_hash, role, related_id) VALUES ('ahmadrizky', ?, 'student', 'stu_1')", (pwd,))
c.execute("INSERT OR REPLACE INTO academy_students (id, name, dob, category, position, guardian, guardian_wa, photo_path, user_id) VALUES ('stu_1', 'Ahmad Rizky Pratama', '2010-01-01', 'U-12', 'CF', 'Budi', '08123', NULL, 'ahmadrizky')")

# Seed Bill
c.execute("INSERT OR REPLACE INTO finance_bills (id, student_id, month, amount, status) VALUES ('bill_1', 'stu_1', 'Februari 2026', 150000, 'unpaid')")

# Seed Report
scores = json.dumps({"passing": 80, "shooting": 75, "stamina": 90, "attitude": 100})
c.execute("INSERT OR REPLACE INTO academy_attendance (id, date, student_id, status) VALUES ('att_1', '2026-02-01', 'stu_1', 'present')")
c.execute("INSERT OR REPLACE INTO academy_evaluations (id, month, student_id, data) VALUES ('eval_1', '2026-02', 'stu_1', ?)", (scores,))

conn.commit()
conn.close()
print("Seeded.")
