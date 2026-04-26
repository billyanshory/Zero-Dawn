import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Replace metrics endpoint
old_metrics = """@app.get("/metrics")
async def get_metrics(request: Request):
    require_admin(request)
    # Simple JSON representation for now
    return response.json({
        "browser_pool_available": browser_pool.queue.qsize(),
        "concurrent_scans": Config.MAX_CONCURRENT_SCANS - scan_semaphore._value if hasattr(scan_semaphore, '_value') else 0
    })"""

new_metrics = """@app.get("/metrics")
async def get_metrics(request: Request):
    require_admin(request)
    # Simple JSON representation for now
    return response.json({
        "browser_pool_available": browser_pool.queue.qsize() if getattr(browser_pool, '_initialized', False) else 0,
        "concurrent_scans": _active_scan_count
    })"""

content = content.replace(old_metrics, new_metrics)

# Inject into scrape_url_with_playwright
old_scrape_sig = """async def scrape_url_with_playwright(url: str) -> str:
    await browser_pool.ensure_initialized()
    async with scan_semaphore:"""

new_scrape_sig = """async def scrape_url_with_playwright(url: str) -> str:
    global _active_scan_count
    await browser_pool.ensure_initialized()
    async with scan_semaphore:
        _active_scan_count += 1
        try:"""

content = content.replace(old_scrape_sig, new_scrape_sig)

# We need to add the finally block for the new try block.
# The original structure:
#    async with scan_semaphore:
#        browser = None
#        try:
#            ...
#        finally:
#            if browser is not None:
#                await browser_pool.put(browser)
#
# Now it will be:
#    async with scan_semaphore:
#        _active_scan_count += 1
#        try:
#            browser = None
#            try:
#                ...
#            finally:
#                if browser is not None:
#                    await browser_pool.put(browser)
#        finally:
#            _active_scan_count -= 1

old_bottom = """        finally:
            if browser is not None:
                await browser_pool.put(browser)"""

new_bottom = """            finally:
                if browser is not None:
                    await browser_pool.put(browser)
        finally:
            _active_scan_count -= 1"""

content = content.replace(old_bottom, new_bottom)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
