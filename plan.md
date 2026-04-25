1. **Fix 'Absen Panitia' (Committee Attendance)**:
   - Add a `try/except` block with `db.session.execute(text("ALTER TABLE qurban_attendance ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE"))` before `db.create_all()` in the app setup section. Add `is_verified` to `QurbanAttendance` class.
   - Define `IDUL_ADHA_ABSEN_HTML` string variable containing the new UI for both admin (view attendees, verify them) and regular users (check in, view list of attendees and verifications).
   - Use `replace_with_git_merge_diff` on lines ~2624-2631 to change the 'Absen Panitia' button from a form submitting a POST to a standard link `<a href="/idul-adha/absen">`.
   - Update `idul_adha_absen()` to handle both `GET` and `POST` methods, rendering `IDUL_ADHA_ABSEN_HTML`. Also, add an admin verify route `/admin/idul-adha/absen/verify/<int:id>` to set `is_verified=True`.
   - Add verification checks with `grep -c` and AST parse to ensure syntax is valid after these edits.

2. **Fix 'Laporan Qurban' (Qurban Report)**:
   - Use `replace_with_git_merge_diff` to inject the `async function submitQurbanStats(event)` in `IDUL_ADHA_LAPORAN_HTML` script tag, reading inputs and POSTing to `/api/qurban/stats/update`.
   - Insert new route `@app.route('/api/qurban/stats/update', methods=['POST'])` decorated with `@csrf.exempt` before or after `api_qurban_stats`.
   - Verify syntax.

3. **Fix 'Daftar Shohibul' (Shohibul PIN List)**:
   - Add `@csrf.exempt` above `@app.route('/api/qurban/shohibul/generate_pin', methods=['POST'])`.
   - Update `IDUL_ADHA_HEWAN_ADMIN_HTML` container (around line 2963) to use `pt-20 md:pt-24` class so it drops below the top navbar.
   - Verify syntax.

4. **Fix 'Pembagian' (Distribution)**:
   - Run raw SQL to alter `distribusi_kupon` table: `ALTER TABLE distribusi_kupon CHANGE nik nama_kepala_keluarga VARCHAR(255) NOT NULL`. Change `DistribusiKupon.nik` to `DistribusiKupon.nama_kepala_keluarga` in the class definition.
   - Around lines 3526 and 3690, replace 'NIK (Nomor Induk Kependudukan)', 'NIK', and 'warga_nik' with 'Nama Lengkap Kepala Keluarga' and 'nama_kepala_keluarga', remove the 16 digit pattern requirement.
   - Around line 3690, delete the duplicate block starting with `Hindari antrean panjang. Cek jadwal pengambilan daging qurban RT Anda di sini...`.
   - Add `pt-20 md:pt-24` styling to the container at the top of the admin view for Kupon (around line 3350).
   - Add `@csrf.exempt` to `@app.route('/api/qurban/pembagian/generate_kupon', methods=['POST'])`.
   - Update logic in `api_qurban_generate_kupon` to look for `nama_kepala_keluarga` instead of `nik`, and remove `nik.isdigit()` checks.
   - Update `api_qurban_list_kupons` to use `nama_kepala_keluarga` and mask it like `k.nama_kepala_keluarga[:3] + '***' + k.nama_kepala_keluarga[-3:]`.
   - Verify syntax.

5. **Fix 'Peta Distribusi'**:
   - Fix `admin_qurban_peta` route aggregation logic: `total_quota = sum([s.total_quota or 0 for s in slots])` and `total_distributed = sum([s.distributed_count or 0 for s in slots])` to prevent 500 crashes.
   - Verify syntax.

6. **Verify and Start Application**:
   - Verify the syntax of the entire `app.py` file using `python3 -c "import ast; ast.parse(open('app.py').read())"`.
   - Check UI formatting and endpoints via Playwright script or a quick local Flask run to ensure fixing 500s worked.

7. **Pre-commit Instructions**:
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.

8. **Submit Changes**:
   - Submit the modifications with a descriptive commit message.
