plan = """
1. **Replace Tailwind CDN JIT compiler with pre-built CSS link**
   - In `app.py`, locate the `<script src="https://cdn.tailwindcss.com"></script>` and the `tailwind.config` script block.
   - Replace them with `<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3/dist/tailwind.min.css" rel="stylesheet">`.
2. **Add Flask-Compress for HTTP response compression**
   - Add `from flask_compress import Compress` to the imports in `app.py`.
   - Add `Compress(app)` immediately after `app = Flask(__name__)`.
3. **Fix `.limit()` before `.order_by()` bug**
   - In `ramadhan_dashboard` (around line 7020), replace `StudentPortfolio.query.limit(100).order_by(StudentPortfolio.created_at.desc()).all()` with `StudentPortfolio.query.order_by(StudentPortfolio.created_at.desc()).limit(100).all()`.
4. **Fix unbounded `.all()` query in `api_tunalaras_guru_monitor`**
   - Replace the `EmotionJournal` query that fetches all rows and groups them in Python with a SQL-level aggregation subquery.
   - Use `func.count` and `func.max` to aggregate by `anak_id`.
   - Join with the `Siswa` model and paginate the results.
5. **Add route-level caching**
   - Add `@cache.cached()` decorators to semi-static routes (`/slb/tunanetra`, `/slb/tunarungu`, etc.) with a 3600-second timeout.
   - Add `@cache.cached()` decorators to data-driven pages (home page, dashboards) with a 30-to-60-second timeout.
6. **Add Eager Loading (N+1 query fix)**
   - Add `from sqlalchemy.orm import joinedload` to imports.
   - In dashboards like `kepala_sekolah_dashboard` and `validator_dashboard`, use `options(joinedload(AkunPengguna.anak))` on queries.
7. **Add missing indexes**
   - Add `Index` and `index=True` for `created_at` in `ReactionTimeLog`, `KognitifEmosiLog`, and `KognitifBentukLog`.
   - Add composite index for `EmotionJournal`.
8. **Optimize External Assets**
   - Replace Font Awesome `all.min.css` with `solid.min.css`.
   - Reduce Google Fonts weights and conditionally load `Amiri`.
9. **Conditionally load Socket.IO and Canvas Confetti**
   - Wrap the Socket.IO `<script>` tag in a Jinja `{% if needs_socketio %}` block.
   - Move `canvas-confetti` `<script>` tags to be dynamically loaded when the user actually starts the game.
10. **Defer Audio Preloading**
    - Add `preload="none"` to `<audio>` elements.
    - Avoid instantiating `new Audio()` directly on page load.
11. **Fix Unbounded Queries in Schedulers/APIs**
    - Apply `.yield_per(50)` or filter to relevant rows in the scheduler's medication notification job for `PushSubscription`.
    - Add `.limit(100)` to the medication schedule API.
12. **Optimize Emoji Prefetching**
    - Disable the background Twemoji CDN download in `prefetch_emoji_icons` to prevent eventlet blocking.
13. **Fix Cache Invalidation and `db.create_all()`**
    - Use `cache.delete_memoized(get_settings)` for memoized caches.
    - Wrap `db.create_all()` behind an environment variable (`FLASK_INIT_DB`).
14. **Add Cache-Control Headers**
    - Implement an `@app.after_request` handler to set `Cache-Control` headers.
15. **Pre-commit Instructions**
    - Ensure proper testing, verification, review, and reflection are done before committing.
16. **Submit**
    - Submit the finalized code with the fixes applied.
"""
with open('plan.md', 'w') as f:
    f.write(plan)
