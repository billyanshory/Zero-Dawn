1. **Define `now_wita` function**:
    - Add a global `now_wita()` function that properly gets the current time in the `Asia/Makassar` timezone, as memory explicitly dictates: `For timestamps in the masjid-al-hijrah application, universally use a timezone-aware helper like now_wita() configured for WITA (Asia/Makassar)`.
    - Function:
      ```python
      def now_wita():
          makassar_tz = pytz.timezone('Asia/Makassar')
          return datetime.datetime.now(makassar_tz)
      ```
    - Since `check_in_time` is stored as naive datetime (or UTC, though when saved using `datetime.datetime.now(makassar_tz)` it might strip timezone information depending on how SQLAlchemy handles it). To be perfectly safe, as per the memory explicitly states: "strictly localize them to WITA (e.g., `pytz.utc.localize(dt).astimezone(pytz.timezone('Asia/Makassar'))`) before calling `.strftime()` to prevent incorrect UTC offset displays."
    - Wait, if we use `now_wita()`, saving to the database using `u.check_in_time = current_time` will save a timezone-aware datetime. Wait, Postgres `TIMESTAMP` without timezone will store it naive. If it's saved as local time but without timezone, when retrieved, formatting it directly via `.strftime()` might be correct if it didn't do UTC conversion. But the prompt says the time generated was 23:55 when tested at 06:00-09:00. This is approximately an 8-hour difference backwards (since 07:55 - 8 hours = 23:55 yesterday). This clearly means the server is treating the stored time as UTC and applying an offset or the time was stored as UTC naive but generated as UTC naive instead of local.
    - If `datetime.datetime.now(makassar_tz)` returns an aware datetime, saving to a `TIMESTAMP` without timezone column stores it in UTC in Postgres (because the driver converts aware to UTC). When retrieved, it's a naive datetime in UTC. We *must* explicitly convert it back.
    - So, when displaying `p.check_in_time`:
      ```python
      makassar_tz = pytz.timezone('Asia/Makassar')
      check_in_dt_wita = pytz.utc.localize(u.check_in_time).astimezone(makassar_tz)
      formatted_time = check_in_dt_wita.strftime("%H:%M")
      ```

2. **Add `foto_profil` to `QurbanAttendance` Model & Schema update**:
    - Add `foto_profil = db.Column(db.String(255), nullable=True)` to `QurbanAttendance` model.
    - At the bottom of the script, where schemas are checked:
      ```python
      try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN foto_profil VARCHAR(255) NULL"))
      except Exception: pass
      ```

3. **Digital ID Card - Add Profile Picture & Edit Pencil UI**:
    - Add an interactive pencil icon over the profile picture in `#idCardWrapper`.
    - Update the placeholder default profile picture to use the new `user.foto_profil` if available.
    - Modify the `fetch` to get the profile picture.
    - Create a modal for changing/saving the profile picture inside `IDUL_ADHA_ABSEN_PANITIA_HTML`.

4. **Digital ID Card - Fix Text Overflow (UI/UX)**:
    - Adjust `#idCardWrapper` styles. Instead of fixed constraints, ensure `break-words` and `min-h-[350px]` or `min-h-fit` are used so text doesn't flow out.

5. **Create Profile Picture Upload Route**:
    - Create `POST /idul-adha/absen-panitia/upload-foto`.
    - Receives Base64 image, saves it (or stores the path) and updates `foto_profil` for the current user's session.
    - Actually, since the app must stay a single file and the DB is Postgres, saving Base64 strings directly in `foto_profil` string column? A String(255) might be too small for Base64. A `db.Text` would be needed if storing Base64, but usually, saving the file to `static/uploads/` is better. Wait, the prompt memory says "The only acceptable supporting artifacts are `.env`, `lexicon.json`, `requirements.txt`, and an optional `static/` directory." We can save it to `static/uploads/profiles/`. Or we can just use `db.Text`. Let's store Base64 directly as `db.Text` to keep it simple, or `db.Column(db.Text)` and avoid file system permission issues in production. Wait, if I alter `foto_profil` to `TEXT`, it can hold base64. Let's use `TEXT`.

6. **Pre-commit Checks**: Run checks.

Let's do `request_plan_review` first.
