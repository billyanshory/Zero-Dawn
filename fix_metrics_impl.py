import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Add _active_scan_count below scan_semaphore
old_sem = "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n\n@app.before_server_start"
new_sem = "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n_active_scan_count = 0\n\n@app.before_server_start"
if "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n_active_scan_count = 0" not in content:
    content = content.replace(
        "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n",
        "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n_active_scan_count = 0\n"
    )

old_scrape = """async def scrape_url_with_playwright(url: str) -> str:
    await browser_pool.ensure_initialized()
    async with scan_semaphore:"""

new_scrape = """async def scrape_url_with_playwright(url: str) -> str:
    global _active_scan_count
    await browser_pool.ensure_initialized()
    async with scan_semaphore:
        _active_scan_count += 1
        try:"""

# We need to be careful with the indentation since we are wrapping `browser = None` ... etc. in a try/finally
# Let's use a Python AST or regex approach to surgically inject this.
