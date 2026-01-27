from playwright.sync_api import sync_playwright
import time

def verify_clinic(page):
    try:
        page.goto("http://localhost:5000", timeout=10000)
    except Exception as e:
        print(f"Failed to load page: {e}")
        return

    # Check if redirected to Queue page logic (title should be ANTREAN in navbar, and page title should be Antrean Klinik)
    # The page title in HTML_QUEUE is <title>Antrean Klinik</title>
    title = page.title()
    print(f"Page title: {title}")

    # Check for Horizontal Menu
    menu = page.locator(".medical-horizontal-menu")
    if menu.is_visible():
        print("Horizontal menu is visible")
    else:
        print("Horizontal menu NOT visible")

    # Check for specific buttons
    expect_buttons = ["Antrean", "Rekam Medis", "Stok Obat", "Profil Klinik", "Surat Sakit", "Kasir", "Data Pasien", "Cari Pasien", "Statistik"]
    found_all = True
    for btn_text in expect_buttons:
        # Note: text-transform: uppercase is CSS, but locator might match text content in DOM.
        # The HTML has spans with Title Case e.g. <span>Antrean</span>
        btn = page.locator(f".feature-btn span:text-is('{btn_text}')")
        if not btn.count():
             print(f"Button '{btn_text}' not found")
             found_all = False

    if found_all:
        print("All buttons found")

    # Check Left Logo
    logo = page.locator(".medical-logo-icon.fas.fa-clinic-medical")
    if logo.is_visible():
        print("Home Logo is visible")
    else:
        print("Home Logo NOT visible")

    # Take screenshot
    page.screenshot(path="verification_screenshot.png")
    print("Screenshot taken: verification_screenshot.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 412, 'height': 915}) # Mobile viewport
        try:
            verify_clinic(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
