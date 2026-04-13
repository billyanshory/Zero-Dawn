1. **Add `import pytz` and `import uuid`** near the top of the file.
2. **Finding F11**: Add `# ACCEPTED RISK: UUID filenames prevent enumeration. Public access needed for /galeri images.` before `@app.route('/uploads/<filename>')`.
3. **Finding F15**: Fix 4 `return "Unauthorized", 403` lines to return JSON:
   - Line 4670 (inside `therapy_log()`)
   - Line 5188 (inside `generate_iep()`)
   - Line 5439 (inside `upload_portfolio()`)
   - Line 10612 (inside `download_modul()`)
4. **Finding F9**: Add `# DESIGN DECISION: Teachers/admin see all students' chart data when no anak_id filter is specified.` at line 10251 in `get_ot_chart_data()`.
5. **Finding F10**: Add `# DESIGN DECISION: Admin/teachers see all nutrition data when no anak_id filter is specified.` at line 10420 in `handle_ot_nutrisi()`.
6. **Finding 12**: Update SocketIO CORS configuration to handle empty env properly (allow '*').
7. **Finding 03**: Update `const socket = io();` to `const socket = (typeof io !== 'undefined') ? io() : null;` and wrap `socket.on('receive_frequency', ...)` with `if (socket) { ... }`.
8. **Finding 14**: Add `# NOTE: In-memory only. Single-worker eventlet required. For multi-worker, migrate to Redis pub/sub via Flask-SocketIO message_queue.` at `connected_clients_dict = {}`.
9. **Finding 11**: Add `return False` in `except Exception:` block of `handle_connect()`.
10. **Finding 15**: Remove `const medSocket = io();` in parent dashboard and update its socket event handler to reuse `socket`.
11. **Finding 16**: Add `if not VAPID_PUBLIC_KEY:` check returning 503 JSON inside `vapid_public_key()`.
12. **Finding 07 & 13**: Refactor `send_web_push()` to take `subscription_id=None`, offload to `eventlet.tpool.execute()`, and update `PushSubscription.last_used`.
13. **Finding 06**: Rename `send_all_pushes` to `send_all_pushes_only`, remove `socketio.emit` from it (moved to `check_medications`), and spawn it as an eventlet green thread.
14. **Findings 01, 02, 04, 09, 06, 07**: Refactor `check_medications()` completely to handle timezone, midnight wraps, correct `OR` logic for medications, remove 500 limit on push subscriptions, order by `id`, emit `socketio` inline, and spawn push background task.
15. **Finding 08**: Update APScheduler configurations to add `max_instances=1`, `coalesce=True`, and `misfire_grace_time`.
16. **Finding 05**: Update `start_scheduler_if_primary()` to use shorter redis TTL and a renewal loop thread.
17. Run pre_commit checks and submit.
