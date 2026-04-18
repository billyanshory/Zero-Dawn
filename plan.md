1. **Phase 1: Deployment Guards**
   - Add `ProxyFix` middleware right after `app = Flask(__name__)`.
   - Update `if __name__ == '__main__':` block to enforce defense-in-depth, strictly checking `FLASK_ENV` and production indicators before allowing the development server to boot, and warning if `socketio.run` is used in production.
   - Refactor `SESSION_COOKIE_SECURE`, `REMEMBER_COOKIE_SECURE`, and `REMEMBER_COOKIE_HTTPONLY` to depend on `_is_dev_env`.
   - Refactor `SocketIO` initialization to properly parse `ALLOWED_ORIGINS` without wildcards in production, set up `message_queue` with `REDIS_URL`, and disable debug logging.

2. **Phase 2: Operator Visibility**
   - Implement `/healthz` and `/readyz` endpoints with `@csrf.exempt` and `limiter.exempt` before `add_security_headers`.
   - Rebuild logging setup to output to `stdout` with `X-Request-ID` injection via a `logging.Filter` and `g.request_id`, add `X-Request-ID` in `after_request`, and optionally configure Sentry.
   - Expand `add_security_headers` to inject robust headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, etc.) depending on content type (HTML vs JSON).

3. **Phase 3: Edge Robustness**
   - Re-implement `@app.errorhandler` for specific HTTP codes (400, 401, 403, 404, 405, 413, 429, 500, 502, 503, 504), returning JSON or HTML based on the request's `Accept` or `Content-Type`.
   - Add `_graceful_shutdown` logic (using `signal` and `atexit`) to terminate the scheduler, close DB connections, delete Redis locks, and flush logs gracefully.
   - Add a fallback mechanism for `Flask-Compress` and properly configure its size, levels, and algorithms.

4. **Phase 4: Configuration Hygiene**
   - Remove the `30-10-50` fallback for `BRANKAS_KODE`, returning 503 when unset.
   - Add a `PUSH_NOTIFICATIONS_ENABLED` derived boolean and block push notification endpoints with 503 if VAPID keys are missing.
   - Parameterize `UPLOAD_FOLDER` and add a startup write-probe check.
   - Adjust `SQLALCHEMY_ENGINE_OPTIONS` using `WEB_CONCURRENCY` and `DB_MAX_CONNECTIONS` to calculate `pool_size` and `max_overflow`.
   - Migrate `_settings_cache` to `Flask-Caching`'s `@cache.memoize(timeout=1800)` and implement `invalidate_settings_cache`.

5. **Phase 5: Eventlet Correctness**
   - Refactor `/api/yasin` to use `requests.get` with timeouts instead of `urllib.request`.
   - Refactor `prefetch_emoji_icons` to use `eventlet.spawn()`, add an `OSError` guard on `os.makedirs`, use `requests.get`, and implement leader-election via Redis.

6. **Phase 6: Schema Evolution Remediation**
   - Add `Flask-Migrate`.
   - Initialize `migrate = Migrate(app, db, ...)`.
   - Refactor `FLASK_INIT_DB` to only run `db.create_all()` in development, and use `flask_migrate`'s `upgrade()` when `FLASK_AUTO_UPGRADE=1`.

7. **Pre-commit and Final Audit**
   - Follow instructions from `pre_commit_instructions`.
   - Check all grep assertions explicitly specified by the user.
