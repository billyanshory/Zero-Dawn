import os
from playwright.sync_api import sync_playwright

os.makedirs('/tmp/verification', exist_ok=True)

def verify(page):
    # 1. Landing Page
    print("Checking Landing Page...")
    page.goto("http://localhost:5000/")
    page.wait_for_selector(".glass-panel")

    # Check H1 removal (specifically the one in glass-panel)
    # The original H1 was <h1 class="mb-4 fw-bold">KLINIK KESEHATAN</h1> inside .glass-panel
    h1_in_panel = page.locator(".glass-panel > h1")
    count = h1_in_panel.count()

    if count > 0:
        text = h1_in_panel.inner_text()
        if "KLINIK KESEHATAN" in text:
            print("FAIL: H1 KLINIK KESEHATAN still exists in glass-panel!")
        else:
            print(f"INFO: Found H1 in glass-panel but text is '{text}'")
    else:
        print("PASS: No H1 found in glass-panel (KLINIK KESEHATAN removed).")

    # Check Status UI
    page.wait_for_selector("#status-container .status-badge")
    print("PASS: Status badge found.")

    page.screenshot(path="/tmp/verification/landing.png")

    # 2. Rekam Medis
    print("Checking Rekam Medis...")
    page.goto("http://localhost:5000/rekam-medis")

    # Check Nama Pasien header
    # We look for th with text "Nama Pasien" and check attribute style
    th = page.locator("th", has_text="Nama Pasien")
    # Wait for it to be attached
    th.wait_for()

    style = th.get_attribute("style") or ""
    # Normalize spaces
    clean_style = style.replace(" ", "").lower()
    if "white-space:nowrap" in clean_style:
        print(f"PASS: Nama Pasien style is '{style}'")
    else:
        print(f"FAIL: Nama Pasien style is '{style}'")

    page.screenshot(path="/tmp/verification/rekam_medis.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
