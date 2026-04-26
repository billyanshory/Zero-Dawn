import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Add _active_scan_count below scan_semaphore
if "_active_scan_count = 0" not in content:
    content = content.replace(
        "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n",
        "scan_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCANS)\n_active_scan_count = 0\n"
    )

# Extract the full scrape_url_with_playwright text by reading up to the next def
match = re.search(r'(async def scrape_url_with_playwright.*?)\ndef sanitize_for_llm', content, re.DOTALL)
if match:
    old_code = match.group(1)

    new_code = """async def scrape_url_with_playwright(url: str) -> str:
    global _active_scan_count
    await browser_pool.ensure_initialized()
    async with scan_semaphore:
        _active_scan_count += 1
        try:
            browser = None
            try:
                browser = await browser_pool.get()
                async def scrape_inner():
                    profile = secrets.choice(DEVICE_PROFILES)
                    context_kwargs = {
                        "viewport": profile["viewport"],
                        "user_agent": profile["user_agent"],
                        "java_script_enabled": True,
                        "ignore_https_errors": False,
                        "locale": "id-ID",
                        "timezone_id": "Asia/Makassar",
                        "geolocation": {"latitude": -0.502, "longitude": 117.153},
                        "permissions": ["geolocation"],
                        "color_scheme": "light",
                        "device_scale_factor": profile["device_scale_factor"],
                        "is_mobile": profile["is_mobile"],
                        "has_touch": profile["has_touch"],
                        "extra_http_headers": {
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                            "Sec-CH-UA-Mobile": "?1" if profile["is_mobile"] else "?0",
                            "Sec-CH-UA-Platform": profile["Sec-CH-UA-Platform"]
                        }
                    }

                    if Config.PROXY_URL:
                        context_kwargs["proxy"] = {"server": Config.PROXY_URL}
                        if Config.PROXY_USERNAME:
                            context_kwargs["proxy"]["username"] = Config.PROXY_USERNAME
                            context_kwargs["proxy"]["password"] = Config.PROXY_PASSWORD

                    context = await browser.new_context(**context_kwargs)

                    stealth_script = \"\"\"
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Google Inc. (Intel)';
                        if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        return originalGetParameter(parameter);
                    };
                    const originalDebug = console.debug;
                    console.debug = function() { if(arguments[0] !== 'debugger') originalDebug.apply(console, arguments); };
                    \"\"\"
                    await context.add_init_script(stealth_script)
                    await context.route("**/*", abort_private_routes)

                    page = await context.new_page()
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                        # Stabilization phase
                        try:
                            await page.wait_for_function("document.readyState === 'complete'", timeout=10000)
                        except Exception:
                            pass

                        # Scroll sequence
                        for _ in range(5):
                            await page.evaluate("window.scrollBy(0, document.body.scrollHeight / 5)")
                            await asyncio.sleep(0.3)
                        await asyncio.sleep(2.0)
                        await page.evaluate("window.scrollTo(0, 0)")
                        await page.mouse.move(100, 100)
                        await page.mouse.move(200, 200, steps=10)

                        extract_script = \"\"\"
                        () => {
                            function extractText(root) {
                                let text = '';
                                if (!root) return text;

                                if (root.nodeType === Node.TEXT_NODE) {
                                    return root.textContent + ' ';
                                }

                                if (root.nodeType === Node.ELEMENT_NODE) {
                                    const style = window.getComputedStyle(root);
                                    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0 || style.fontSize === '0px') {
                                        return text;
                                    }

                                    if (root.tagName === 'NOSCRIPT' || root.tagName === 'SCRIPT' || root.tagName === 'STYLE') {
                                        return text;
                                    }

                                    const before = window.getComputedStyle(root, '::before').getPropertyValue('content');
                                    if (before && before !== 'none' && before !== 'normal') text += before.replace(/['"]/g, '') + ' ';

                                    if (root.shadowRoot) {
                                        text += extractText(root.shadowRoot);
                                    }

                                    if (root.tagName === 'IFRAME') {
                                        try {
                                            if (root.contentDocument) {
                                                text += extractText(root.contentDocument.body);
                                            }
                                        } catch(e) {}
                                    }

                                    if (root.hasAttribute('aria-label')) text += root.getAttribute('aria-label') + ' ';
                                    if (root.hasAttribute('aria-description')) text += root.getAttribute('aria-description') + ' ';
                                    if (root.hasAttribute('alt')) text += root.getAttribute('alt') + ' ';
                                    if (root.hasAttribute('title')) text += root.getAttribute('title') + ' ';
                                    if (root.tagName === 'META' && (root.name === 'description' || root.getAttribute('property')?.startsWith('og:'))) {
                                        text += root.content + ' ';
                                    }

                                    for (let child of root.childNodes) {
                                        text += extractText(child);
                                    }

                                    const after = window.getComputedStyle(root, '::after').getPropertyValue('content');
                                    if (after && after !== 'none' && after !== 'normal') text += after.replace(/['"]/g, '') + ' ';
                                }
                                return text;
                            }
                            return extractText(document);
                        }
                        \"\"\"
                        text_content = await page.evaluate(extract_script)

                        ocr_text = ""
                        if Config.OCR_ENABLED:
                            try:
                                images = await page.locator("img, [style*='background-image']").all()
                                for img in images[:30]:
                                    try:
                                        box = await img.bounding_box()
                                        if box and box["width"] > 50 and box["height"] > 50 and box["width"] * box["height"] < 5000000:
                                            screenshot_bytes = await img.screenshot(type="jpeg", quality=80)
                                            image = Image.open(io.BytesIO(screenshot_bytes))
                                            loop = asyncio.get_event_loop()
                                            try:
                                                extracted = await asyncio.wait_for(
                                                    loop.run_in_executor(None, partial(pytesseract.image_to_string, image, lang="ind+eng")),
                                                    timeout=10.0
                                                )
                                                ocr_text += " " + extracted.strip()
                                            except asyncio.TimeoutError:
                                                logger.warning("OCR timed out on an image")
                                                continue
                                    except Exception:
                                        continue
                            except Exception as e:
                                logger.warning(f"OCR Pass failed: {e}")

                        page_title = await page.title()

                        full_text = f"Page Title: {page_title}\\n\\n{text_content}\\n\\nOCR Text:\\n{ocr_text}"

                        # Normalization
                        full_text = unicodedata.normalize("NFKC", full_text)
                        # Remove zero width characters
                        full_text = re.sub(r'[\\u200b\\u200c\\u200d\\u2060\\ufeff]', '', full_text)
                        full_text = re.sub(r'\\s+', ' ', full_text).strip()

                        if len(full_text) > Config.LLM_MAX_INPUT_CHARS:
                            logger.warning(f"Truncated scraped text from {len(full_text)} to {Config.LLM_MAX_INPUT_CHARS} chars.")

                        return full_text[:Config.LLM_MAX_INPUT_CHARS]

                    finally:
                        await context.close()

                return await asyncio.wait_for(scrape_inner(), timeout=Config.SCAN_BUDGET_SECONDS)

            except asyncio.TimeoutError:
                raise ValueError("The scan exceeded its overall budget.")
            except PlaywrightTimeoutError:
                raise ValueError("The target website did not respond within the timeframe. It may be offline or blocking automated access.")
            except PlaywrightError as e:
                raise ValueError("Failed to render the target website. The site may use advanced bot detection.")
            except Exception as e:
                logger.error(f"Unexpected error in scrape_url_with_playwright for URL={url}", exc_info=True)
                raise Exception("An unexpected error occurred during website scanning.")
            finally:
                if browser is not None:
                    await browser_pool.put(browser)
        finally:
            _active_scan_count -= 1
"""
    content = content.replace(old_code, new_code)

# Update get_metrics
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
if old_metrics in content:
    content = content.replace(old_metrics, new_metrics)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
