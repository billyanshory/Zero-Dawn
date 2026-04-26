import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# For the third time, it looks like my Defect 4, 5, 6, 7 changes got dropped during the previous chaotic state! Let's reapply it precisely.

new_vars = """# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------
scan_events: dict[str, list[asyncio.Queue]] = {}
_scan_events_lock = asyncio.Lock()

def publish_scan_event(scan_id: str, status: str):
    if scan_id in scan_events:
        for q in scan_events[scan_id]:
            try:
                q.put_nowait(status)
            except asyncio.QueueFull:
                pass

@app.get("/")"""

content = content.replace("# -----------------------------------------------------------------------------\n# ROUTES\n# -----------------------------------------------------------------------------\n@app.get(\"/\")", new_vars)

# Remove duplicate publish calls in api_scan
old_api_scan = """        try:
            # We don't commit SCANNING/ANALYZING to save DB roundtrips, SSE can track logical progress client-side
            publish_scan_event(scan_id, ScanStatus.SCANNING.value)
            publish_scan_event(scan_id, ScanStatus.SCANNING.value)
            scraped_text = await scrape_url_with_playwright(valid_url)
            log_entry.raw_page_text = scraped_text

            publish_scan_event(scan_id, ScanStatus.ANALYZING.value)
            publish_scan_event(scan_id, ScanStatus.ANALYZING.value)
            analysis = await analyze_text_with_llm(scraped_text)"""

new_api_scan = """        try:
            # We don't commit SCANNING/ANALYZING to save DB roundtrips, SSE can track logical progress client-side
            publish_scan_event(scan_id, ScanStatus.SCANNING.value)
            scraped_text = await scrape_url_with_playwright(valid_url)
            log_entry.raw_page_text = scraped_text

            publish_scan_event(scan_id, ScanStatus.ANALYZING.value)
            analysis = await analyze_text_with_llm(scraped_text)"""

if old_api_scan in content:
    content = content.replace(old_api_scan, new_api_scan)

# Fix scan_stream synchronization and connection issues
old_scan_stream = """async def scan_stream(request: Request, scan_id: str):
    response_stream = await request.respond(content_type="text/event-stream")

    q = asyncio.Queue()
    if scan_id not in scan_events:
        scan_events[scan_id] = []
    scan_events[scan_id].append(q)

    try:
        while True:
            try:
                status = await asyncio.wait_for(q.get(), timeout=15.0)
                await response_stream.send(f"data: {json.dumps({'status': status})}\\n\\n")
                if status in ["completed", "error"]:
                    break
            except asyncio.TimeoutError:
                # Keep-alive heartbeat
                await response_stream.send(": heartbeat\\n\\n")
    finally:
        if scan_id in scan_events:
            if q in scan_events[scan_id]:
                scan_events[scan_id].remove(q)
            if not scan_events[scan_id]:
                del scan_events[scan_id]"""

new_scan_stream = """async def scan_stream(request: Request, scan_id: str):
    response_stream = await request.respond(content_type="text/event-stream")

    q = asyncio.Queue()
    async with _scan_events_lock:
        if scan_id not in scan_events:
            scan_events[scan_id] = []
        scan_events[scan_id].append(q)

    try:
        async def stream_loop():
            while True:
                try:
                    status = await asyncio.wait_for(q.get(), timeout=15.0)
                    try:
                        await response_stream.send(f"data: {json.dumps({'status': status})}\\n\\n")
                    except (ConnectionResetError, BrokenPipeError):
                        break
                    if status in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    try:
                        await response_stream.send(": heartbeat\\n\\n")
                    except (ConnectionResetError, BrokenPipeError):
                        break

        await asyncio.wait_for(stream_loop(), timeout=Config.SCAN_BUDGET_SECONDS + 60)
    except asyncio.TimeoutError:
        pass
    finally:
        async with _scan_events_lock:
            if scan_id in scan_events:
                if q in scan_events[scan_id]:
                    scan_events[scan_id].remove(q)
                if not scan_events[scan_id]:
                    del scan_events[scan_id]"""

if old_scan_stream in content:
    content = content.replace(old_scan_stream, new_scan_stream)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
