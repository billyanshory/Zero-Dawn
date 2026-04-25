# GambitHunter Runbook

## Deployment
GambitHunter is a single-file monolith (`app.py`). Deploy using a standard systemd service running Sanic workers, e.g.:

```
ExecStart=/path/to/venv/bin/python app.py
```

## Scaling
Scaling is vertical primarily, bounded by RAM. Increase `APP_WORKERS` to scale Sanic handling, but be aware that each worker maintains a `BROWSER_POOL_SIZE` subset. Total headless Chromium instances = `APP_WORKERS * BROWSER_POOL_SIZE`. Ensure the IDCloudHost VM has sufficient RAM (min 150-300MB per Chromium instance).

## Monitoring
Check `/health` and `/readiness` for liveness probes. Access `/metrics` (requires `ADMIN_API_KEY`) for Prometheus-style metrics. Check logs (structured JSON) for internal errors.
