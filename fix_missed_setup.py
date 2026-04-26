import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Since I ran `git checkout HEAD`, all my previous fixes from Defect 2 (setup_app, start_background_tasks) were lost!
# Let's re-apply them.

# 1. Setup app listeners
old_start_background_tasks = """@app.before_server_start
async def start_background_tasks(app, loop):
    app.add_task(cleanup_rate_limits_db())

    # Recover pending scans
    async with get_db_session() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=Config.SCAN_BUDGET_SECONDS * 2)
        result = await session.execute(
            select(ScanLog).where(
                ScanLog.scan_status.in_([ScanStatus.PENDING, ScanStatus.SCANNING, ScanStatus.ANALYZING]),
                ScanLog.updated_at < cutoff
            )
        )
        stuck_scans = result.scalars().all()
        for scan in stuck_scans:
            scan.scan_status = ScanStatus.ERROR
            scan.internal_error_detail = "Process restarted mid-scan"
            scan.user_facing_error = "Server terhenti saat memindai. Silakan coba lagi."
        await session.commit()"""

if old_start_background_tasks in content:
    content = content.replace(old_start_background_tasks, "")

old_setup_app = """@app.before_server_start
async def setup_app(app, loop):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully")
    await browser_pool.initialize()
    logger.info("Browser pool initialized")"""

new_setup_app = """@app.before_server_start
async def setup_app(app, loop):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully")

    try:
        async with get_db_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=Config.SCAN_BUDGET_SECONDS * 2)
            result = await session.execute(
                select(ScanLog).where(
                    ScanLog.scan_status.in_([ScanStatus.PENDING, ScanStatus.SCANNING, ScanStatus.ANALYZING]),
                    ScanLog.updated_at < cutoff
                )
            )
            stuck_scans = result.scalars().all()
            for scan in stuck_scans:
                scan.scan_status = ScanStatus.ERROR
                scan.internal_error_detail = "Process restarted mid-scan"
                scan.user_facing_error = "Server terhenti saat memindai. Silakan coba lagi."
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to recover stuck scans during startup: {e}")

    app.add_task(cleanup_rate_limits_db())"""

content = content.replace(old_setup_app, new_setup_app)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
