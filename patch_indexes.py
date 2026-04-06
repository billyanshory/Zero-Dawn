import sqlite3

conn = sqlite3.connect('slb.db')
c = conn.cursor()
c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
indexes = c.fetchall()
for index in indexes:
    print(index)
conn.close()
