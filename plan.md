1. **Replace Tailwind CDN script**
   - Replace the Tailwind CDN JIT script and the `tailwind.config` configuration with the pre-built CSS link (`<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3/dist/tailwind.min.css" rel="stylesheet">`) in `sekolah-luar-biasa-66 ( idcloudhost - Seventh Layer of Quality Control - Umum - Opus 4.6 ).py`.
2. **Verify Tailwind CSS fix**
   - Use `grep` to ensure `cdn.tailwindcss.com` is removed and `cdn.jsdelivr.net/npm/tailwindcss` is added.
3. **Add Flask Compress**
   - Add `from flask_compress import Compress` and `Compress(app)` to the Flask initialization.
4. **Verify Flask Compress fix**
   - Run `python -m py_compile "sekolah-luar-biasa-66 ( idcloudhost - Seventh Layer of Quality Control - Umum - Opus 4.6 ).py"` to check for syntax errors.
5. **Fix `.limit()` before `.order_by()` bug**
   - In `ramadhan_dashboard` (around line 7020), reverse the order of `.limit(100)` and `.order_by()`.
6. **Verify `.limit()` fix**
   - Use `grep` to ensure `StudentPortfolio.query.order_by` correctly precedes `.limit(100)`.
7. **Fix unbounded `.all()` query in `api_tunalaras_guru_monitor`**
   - Replace the `EmotionJournal` query with a SQL-level aggregation subquery using `func.count` and `func.max`, joining with `Siswa` model and paginating results.
8. **Verify `api_tunalaras_guru_monitor` fix**
   - Use `python -m py_compile` to check for syntax errors.
9. **Add Route-level Caching**
   - Add `@cache.cached()` decorators to semi-static routes and dashboards with appropriate timeouts and key prefixes.
10. **Verify Route-level Caching**
    - Use `python -m py_compile` to check for syntax errors.
11. **Add Eager Loading (N+1 query fix)**
    - Add `from sqlalchemy.orm import joinedload` to imports and apply `options(joinedload(AkunPengguna.anak))` on queries in `kepala_sekolah_dashboard` and `validator_dashboard`.
12. **Verify Eager Loading**
    - Use `python -m py_compile` to check for syntax errors.
13. **Add Missing Indexes**
    - Add `__table_args__ = (db.Index(...))` and `index=True` for `created_at` in `ReactionTimeLog`, `KognitifEmosiLog`, and `KognitifBentukLog`, and a composite index for `EmotionJournal`.
14. **Verify Missing Indexes**
    - Use `python -m py_compile` to check for syntax errors.
15. **Optimize External Assets & Audio/Socket/Confetti Loading**
    - Replace Font Awesome `all.min.css` with `solid.min.css`.
    - Reduce Google Fonts weights.
    - Wrap the Socket.IO `<script>` tag in a conditional Jinja `{% if needs_socketio %}` block.
    - Defer Audio preloading with `preload="none"`.
16. **Verify Asset Optimizations**
    - Use `grep` to check modified font imports and audio tags.
17. **Optimize Schedulers & APIs**
    - Add `.yield_per(50)` for `PushSubscription` and `.limit(100)` for the medication schedule API.
18. **Verify Schedulers Optimization**
    - Use `python -m py_compile` to check for syntax errors.
19. **Disable Twemoji background fetch & Fix Cache/DB init**
    - Modify `prefetch_emoji_icons` to not fetch from CDN.
    - Use `cache.delete_memoized(get_settings)`.
    - Wrap `db.create_all()` in `if os.environ.get('FLASK_INIT_DB'):`.
20. **Add Cache-Control Headers**
    - Implement `@app.after_request` handler to set `Cache-Control` headers.
21. **Verify Cache & db init fixes**
    - Use `python -m py_compile` to ensure no syntax errors are introduced.
22. **Run tests or start the Flask application**
    - Run tests or start the Flask application to verify that all optimizations work correctly without introducing regressions.
23. **Complete pre-commit steps**
    - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
24. **Submit the change.**
    - Submit the finalized code with the fixes applied.
