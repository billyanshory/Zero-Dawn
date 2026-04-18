The plan is as follows, matching the prompt's phases:

### Phase 1: Foundational deployment guards
1. Import `ProxyFix` from `werkzeug.middleware.proxy_fix`.
2. Wrap `app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)` after `app = Flask(__name__)`.
3. Rebuild the `if __name__ == '__main__':` block to have a production fail-safe and use dynamic IP, port, and `allow_unsafe_werkzeug` according to `FLASK_ENV`. Also check `app.secret_key`. Include the logger line for production advice.
4. Set `SESSION_COOKIE_SECURE` conditionally using `not _is_dev_env`, as well as `REMEMBER_COOKIE_SECURE` and `REMEMBER_COOKIE_HTTPONLY`.
5. Rewrite the `SocketIO` initialization at the top to correctly handle `ALLOWED_ORIGINS`, Redis fanout (`message_queue`), and fallback securely.

### Phase 2: Operator visibility
1. Add `/healthz` and `/readyz` endpoints after `add_security_headers` but before any authentication routes, with `csrf.exempt` and `limiter.exempt`.
2. Rewrite the logging configuration to output to `stdout` with `request_id`, preserve file logging with a fallback, and integrate Sentry dynamically if `SENTRY_DSN` is present. Add `g.request_id` in `before_request` and set the `X-Request-ID` header in `after_request`.
3. Rewrite the security headers middleware (`add_security_headers`) to add extensive headers (HSTS, XCTO, XFO, Referrer-Policy, Permissions-Policy, COOP, CORP) and dynamically branch between HTML and JSON for CSP. Also, strip `Server` and `X-Powered-By`.

### Phase 3: Edge robustness
1. Rewrite `@app.errorhandler(Exception)` and introduce per-status code handlers that return either JSON or HTML based on content type, with `Retry-After` headers where appropriate. Use Indonesian text.
2. Add graceful shutdown logic handling `SIGTERM`, `SIGINT`, and `atexit` that gracefully shuts down APScheduler, releases Redis lock (`slb_scheduler_master`), drains the database pool, and flushes log handlers.
3. Enhance `Flask-Compress` logic to fall back to a minimal gzip `after_request` handler if `flask_compress` is unavailable. Configure Brotli correctly when available.

### Phase 4: Configuration hygiene
1. Remove the fallback for `BRANKAS_KODE` and fail open with 503 if not set.
2. Introduce `PUSH_NOTIFICATIONS_ENABLED` derived from VAPID keys and guard `webpush` routes with a 503 JSON error if disabled.
3. Reconfigure `UPLOAD_FOLDER` to allow environment overrides and implement a writability probe at startup.
4. Parameterize SQLAlchemy connection pool size to calculate `pool_size` and `max_overflow` dynamically from `WEB_CONCURRENCY` and `DB_MAX_CONNECTIONS`.
5. Refactor `_settings_cache` dictionary using `@cache.memoize` to work correctly across multiple workers. Provide `invalidate_settings_cache`.

### Phase 5: Eventlet correctness
1. Replace `urllib.request` in `/api/yasin` with `requests`, handling timeouts properly, and move the `requests` import to the top block.
2. Refactor `prefetch_emoji_icons` to not use daemon `threading.Thread`, but instead use `eventlet.spawn()`. Implement Redis leader election to avoid all workers downloading simultaneously. Handle `makedirs` read-only errors gracefully.

### Phase 6: Schema evolution remediation
1. Import `Migrate` and `alembic_upgrade`.
2. Initialize `Migrate` right after `db` initialization.
3. Replace `FLASK_INIT_DB` block with one that supports both dev creation and `FLASK_AUTO_UPGRADE` using Alembic logic.

### Cross-cutting concerns
- Use `grep -n` before every sed/awk/python change to match lines.
- Validate app starts without errors.
- Ensure `eventlet.monkey_patch()` is untouched at the very top.
- Final checks against the prompt's `grep` requirements.

### Pre-commit
- Complete pre-commit instructions to ensure proper testing, verification, review, and reflection are done.
