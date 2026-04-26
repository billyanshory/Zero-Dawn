import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# I messed up my health fix when I reapplied defect 3/6 and lost my Defect 4 & 5 fixes! Let me reapply them.
old_health = """@app.get("/health")
async def health_check(request: Request):
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        pool_size = browser_pool.queue.qsize() if hasattr(browser_pool, 'queue') else 0
        return response.json({"status": "healthy", "database": "connected", "browser_pool_size": pool_size, "timestamp": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return response.json({"status": "unhealthy", "database": "disconnected", "error": str(e)}, status=503)"""

new_health = """@app.get("/health")
async def health_check(request: Request):
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))

        if not getattr(browser_pool, '_initialized', False):
            pool_status = "lazy_pending"
        elif browser_pool.queue.qsize() > 0:
            pool_status = "ready"
        else:
            pool_status = "exhausted"

        return response.json({"status": "healthy", "database": "connected", "browser_pool": pool_status, "timestamp": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return response.json({"status": "unhealthy", "database": "disconnected", "error": str(e)}, status=503)"""

if old_health in content:
    content = content.replace(old_health, new_health)

old_readiness = """@app.get("/readiness")
async def readiness_check(request: Request):
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        if browser_pool.queue.qsize() == 0 and browser_pool.size > 0:
             return response.json({"status": "not_ready", "reason": "browser_pool_empty"}, status=503)
        return response.json({"status": "ready"})
    except Exception as e:
        return response.json({"status": "not_ready", "reason": "database_error"}, status=503)"""

new_readiness = """@app.get("/readiness")
async def readiness_check(request: Request):
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))

        if not getattr(browser_pool, '_initialized', False):
            return response.json({"status": "ready", "browser_pool": "lazy_pending"})
        elif browser_pool.queue.qsize() > 0:
            return response.json({"status": "ready", "browser_pool": "ready"})
        else:
            return response.json({"status": "not_ready", "reason": "browser_pool_empty"}, status=503)
    except Exception as e:
        return response.json({"status": "not_ready", "reason": "database_error"}, status=503)"""

if old_readiness in content:
    content = content.replace(old_readiness, new_readiness)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
