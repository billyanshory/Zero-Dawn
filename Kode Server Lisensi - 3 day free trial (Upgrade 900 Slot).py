import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DB_FILE = "licenses.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabel Lifetime
    c.execute('''CREATE TABLE IF NOT EXISTS lifetime_keys
                 (key TEXT PRIMARY KEY, hwid TEXT, status TEXT)''')
    # Tabel Trial
    c.execute('''CREATE TABLE IF NOT EXISTS trial_keys
                 (key TEXT PRIMARY KEY, hwid TEXT, status TEXT)''')

    # Masukkan data dummy/awal user (jika belum ada)
    # User Spec: P9AC-EFSZ-GWWP-UBDY | HWID: 48751573395980
    try:
        c.execute("INSERT OR IGNORE INTO lifetime_keys (key, hwid, status) VALUES (?, ?, ?)",
                  ("P9AC-EFSZ-GWWP-UBDY", "48751573395980", "USED"))
    except:
        pass

    # Tambahkan beberapa key trial dummy
    for i in range(10):
        k = f"TRIAL-KEY-{i}"
        c.execute("INSERT OR IGNORE INTO trial_keys (key, hwid, status) VALUES (?, ?, ?)",
                  (k, None, "AVAILABLE"))

    conn.commit()
    conn.close()

init_db()

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.json
        key = data.get('key')
        hwid = data.get('hwid')

        if not key or not hwid:
            return jsonify({"status": "error", "message": "Missing key or hwid"}), 400

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # 1. Cek Lifetime Keys
        c.execute("SELECT hwid FROM lifetime_keys WHERE key=?", (key,))
        row = c.fetchone()

        if row:
            stored_hwid = row[0]
            if stored_hwid is None or stored_hwid == "":
                # Aktivasi Baru
                c.execute("UPDATE lifetime_keys SET hwid=?, status='USED' WHERE key=?", (hwid, key))
                conn.commit()
                conn.close()
                return jsonify({"status": "success", "message": "Lifetime License Activated", "type": "LIFETIME"})
            elif stored_hwid == hwid:
                # Re-aktivasi (User yang sama)
                conn.close()
                return jsonify({"status": "success", "message": "Welcome Back! (Lifetime)", "type": "LIFETIME"})
            else:
                # Terkunci device lain
                conn.close()
                return jsonify({"status": "error", "message": "Key Locked to another Hardware ID"}), 403

        # 2. Cek Trial Keys
        c.execute("SELECT hwid FROM trial_keys WHERE key=?", (key,))
        row = c.fetchone()

        if row:
            stored_hwid = row[0]
            if stored_hwid is None or stored_hwid == "":
                # Aktivasi Trial Baru
                c.execute("UPDATE trial_keys SET hwid=?, status='USED' WHERE key=?", (hwid, key))
                conn.commit()
                conn.close()
                return jsonify({"status": "success", "message": "3-Day Trial Activated", "type": "TRIAL"})
            elif stored_hwid == hwid:
                # Re-aktivasi Trial (User yang sama)
                conn.close()
                return jsonify({"status": "success", "message": "Welcome Back! (Trial)", "type": "TRIAL"})
            else:
                conn.close()
                return jsonify({"status": "error", "message": "Trial Key Locked to another Hardware ID"}), 403

        conn.close()
        return jsonify({"status": "error", "message": "Invalid Serial Number"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)
