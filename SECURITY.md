# Security Configuration

## Proxy Setup
GambitHunter requires a proxy to bypass IP blocks. Configure `PROXY_URL`, `PROXY_USERNAME`, and `PROXY_PASSWORD` in your `.env` file. A residential IP proxy in Indonesia is highly recommended to evade cloaking.

## Rate Limiting
Rate limiting is database-backed. Ensure PostgreSQL is robust to handle atomic upserts under load.

## Admin Endpoints
Admin endpoints (`/admin/*`) are secured by `ADMIN_API_KEY`. Protect this key.
