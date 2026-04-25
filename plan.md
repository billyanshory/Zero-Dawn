1. **Cross-Cutting CSRF Issue**: Add `@csrf.exempt` decorator to the following routes:
   - `api_qurban_stats` (actually wait, is it `api_qurban_stats` or `admin_qurban_stats`? The instruction says add `@csrf.exempt` to `api_qurban_stats` (the POST handler at `/admin/qurban/stats`). Wait, `/admin/qurban/stats` is handled by `admin_qurban_stats` as confirmed by `grep`. I will add to both or just the POST handler as requested. Actually, I will add it to `admin_qurban_stats`, `api_qurban_generate_pin`, `api_qurban_generate_kupon`, `api_qurban_list_kupons`, `qurban_pembagian_cek`, and `qurban_lacak`.) I'll add to `admin_qurban_stats` (POST handler).
2. **Feature 1: Absen Panitia**:
   - Update `QurbanAttendance` model with `verified_by_admin` (Boolean, default False) and `verified_at` (DateTime, nullable).
   - Create `IDUL_ADHA_ABSEN_HTML` template. Includes admin configuration (time window), real-time list with "Verify" toggle, public committee view (check-in button based on window).
   - Update route `/idul-adha/absen` (GET/POST) handling the rendering and attendance logic. Use `pt-20 md:pt-24` top padding.
   - Create route `/admin/qurban/absen/verify/<int:attendance_id>` (POST).
   - In `IDUL_ADHA_DASHBOARD_HTML`, replace the self-submitting form button for Absen Panitia with `<a href="/idul-adha/absen">`.
3. **Feature 2: Laporan Qurban**:
   - In `IDUL_ADHA_LAPORAN_HTML`, add `submitQurbanStats(event)` JS function to collect data and POST to `/admin/qurban/stats`.
   - In `IDUL_ADHA_PEMBAGIAN_ADMIN_HTML`, change "Buat Slot Alokasi" button from `type="button" onclick="submitQurbanStats(event)"` to `type="submit"`.
4. **Feature 3: Daftar Shohibul**:
   - Update PIN generation in `api_qurban_generate_pin` to use the custom alphabet (`"ABCDEFGHJKLMNPQRSTUVWXYZ23456789"`), matching `admin_qurban_hewan_tambah`.
   - In `IDUL_ADHA_LACAK_HTML` (admin panel container): add `pt-24 md:pt-28` to outermost container `div` and remove `justify-center`.
5. **Feature 4: Pembagian**:
   - Rename NIK to "Nama Lengkap Kepala Keluarga" in `IDUL_ADHA_PEMBAGIAN_CEK_HTML` and `IDUL_ADHA_PEMBAGIAN_ADMIN_HTML`. Change IDs, remove `pattern="[0-9]{16}"`, update placeholders.
   - Update backend validations: remove length/digit checks for `nik` in `api_qurban_generate_kupon`, `qurban_pembagian_cek`. Remove NIK masking in `api_qurban_list_kupons` and `showPembagianResult()` in JS.
   - In `IDUL_ADHA_PEMBAGIAN_CEK_HTML` (admin panel container): add `pt-24 md:pt-28` and remove `justify-center`.
   - In `IDUL_ADHA_PEMBAGIAN_CEK_HTML`: Remove the duplicated Jinja form block (`{% if kupon %}...{% else %}...{% endif %}`).
6. **Feature 5: Peta Distribusi**:
   - Create route `/idul-adha/peta` for public map display (read-only). Render `IDUL_ADHA_PETA_DISTRIBUSI_HTML` with `is_admin=session.get('is_admin')`.
   - Update dashboard link in `IDUL_ADHA_DASHBOARD_HTML` to `/idul-adha/peta`.
   - Wrap `DistribusiSlot.query.all()` in try-except returning a graceful error page.
7. **Database Table Creation**:
   - Write a helper in the bottom startup block to drop `QurbanAttendance` table if it exists so `db.create_all()` re-creates it with the new columns, documented clearly with a comment.
8. **Syntax Verification**: Run `python3 -m py_compile` and `python3 -c "import ast; ast.parse(...)"` on the monolithic file.
9. **Functional Verification**: Run Flask app locally to ensure that the code executes correctly.
10. **Pre commit step**: Complete pre commit steps to make sure proper testing, verifications, reviews and reflections are done.
