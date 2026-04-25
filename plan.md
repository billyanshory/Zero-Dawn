1.  **Add `@csrf.exempt`**
    *   Add `@csrf.exempt` decorator to `admin_qurban_stats` (`/admin/qurban/stats`).
    *   Add `@csrf.exempt` decorator to `api_qurban_generate_pin` (`/api/qurban/shohibul/generate_pin`).
    *   Add `@csrf.exempt` decorator to `api_qurban_generate_kupon` (`/api/qurban/pembagian/generate_kupon`).
    *   Add `@csrf.exempt` decorator to `api_qurban_list_kupons` (`/api/qurban/pembagian/list_kupons`).
    *   Add `@csrf.exempt` decorator to `qurban_pembagian_cek` (`/qurban/pembagian/cek`).
    *   Add `@csrf.exempt` decorator to `qurban_lacak` (`/qurban/lacak`).

2.  **Laporan Qurban JavaScript Fixes**
    *   Define `submitQurbanStats(event)` in `IDUL_ADHA_LAPORAN_HTML` script block to send admin form data to `/admin/qurban/stats` via POST.
    *   Change button in `IDUL_ADHA_PEMBAGIAN_ADMIN_HTML` from `type="button" onclick="submitQurbanStats(event)"` to `type="submit"`.

3.  **Absen Panitia Redesign**
    *   Create `IDUL_ADHA_ABSEN_HTML` with admin panel and panitia check-in UI, respecting design system and `pt-20 md:pt-24`.
    *   Update `idul_adha_absen` to handle GET and POST. Store/read attendance time window from `AppSettings`.
    *   Modify `QurbanAttendance` model to add `verified_by_admin` (Boolean, default `False`) and `verified_at` (DateTime, nullable).
    *   Create `/admin/qurban/absen/verify/<int:attendance_id>` endpoint.
    *   Change dashboard button in `IDUL_ADHA_DASHBOARD_HTML` to a simple link `<a href="/idul-adha/absen">`.

4.  **Daftar Shohibul Fixes**
    *   Update `api_qurban_generate_pin` and `admin_qurban_hewan_tambah` to use the same custom alphabet PIN generation: `alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"`.
    *   Fix card positioning in `IDUL_ADHA_LACAK_HTML` by adding `pt-24 md:pt-28` to outermost container and removing `justify-center`.

5.  **Pembagian Kupon Fixes**
    *   Fix card positioning in `IDUL_ADHA_PEMBAGIAN_CEK_HTML` by adding `pt-24 md:pt-28` to outermost container and removing `justify-center`.
    *   Remove Jinja fallback form from `IDUL_ADHA_PEMBAGIAN_CEK_HTML` (`{% if kupon %}...{% endif %}`).
    *   Rename 'NIK Warga' to 'Nama Lengkap Kepala Keluarga' in `IDUL_ADHA_PEMBAGIAN_CEK_HTML` (admin & public forms), `IDUL_ADHA_PEMBAGIAN_ADMIN_HTML`, and Kupon List modal.
    *   Update backend in `api_qurban_generate_kupon`, `api_qurban_list_kupons`, and `qurban_pembagian_cek` to handle text input instead of 16-digit NIK. Remove length/digit validation and masking.

6.  **Peta Distribusi Updates**
    *   Create a public-facing `/idul-adha/peta` route that renders `IDUL_ADHA_PETA_DISTRIBUSI_HTML` in a read-only mode for non-admins.
    *   Update dashboard button in `IDUL_ADHA_DASHBOARD_HTML` to point to `/idul-adha/peta`.
    *   Add proper `pt-20 md:pt-24` padding to `IDUL_ADHA_PANDUAN_HTML` and `IDUL_ADHA_PETA_DISTRIBUSI_HTML`.

7.  **Ensure Table Creation**
    *   Check `db.create_all()` is executed after model definitions to ensure all Qurban tables are created. Because it's an existing file without migration, implement table recreation logic in script for `QurbanAttendance` just to be safe, or let `db.create_all` handle missing tables, but for column addition, raw SQL alter or drop/create. Since user mentioned "dropping and recreating the affected tables should be acceptable", I will drop and recreate `QurbanAttendance`.

8.  **Pre-commit and Test**
    *   Ensure proper testing, verifications, reviews and reflections are done.
