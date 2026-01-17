import os
import time
from playwright.sync_api import sync_playwright

def verify_changes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Navigate to home
        try:
            page.goto("http://localhost:5000", timeout=60000, wait_until="domcontentloaded")
            print("Navigated to home")
        except Exception as e:
            print(f"Failed to navigate: {e}")
            # Try taking screenshot anyway
            page.screenshot(path="verification/error_nav.png")
            return

        # 2. Check Agenda Title
        try:
            title = page.locator("#agenda-latihan .section-title").inner_text()
            print(f"Agenda Title: {title}")
            if "Agenda Latihan & Turnamen" in title:
                print("Title Verification PASSED")
            else:
                print("Title Verification FAILED")
        except Exception as e:
            print(f"Title check failed: {e}")

        # 3. Open Agenda Modal
        try:
            # Find first agenda card
            page.locator("#agenda-latihan .agenda-card-barca").first.click()
            time.sleep(2) # wait for modal animation

            # Take screenshot of Agenda Modal
            os.makedirs("verification", exist_ok=True)
            page.screenshot(path="verification/agenda_modal.png")
            print("Agenda Modal screenshot taken")

            # Close modal
            page.locator("#agenda-modal").click()
            time.sleep(0.5)
        except Exception as e:
            print(f"Agenda Modal check failed: {e}")

        # 4. Main Partners Resize
        try:
            # Scroll to sponsors
            page.locator("#sponsors").scroll_into_view_if_needed()

            # Check slider existence
            slider = page.locator(".custom-range-slider").first
            if slider.count() > 0:
                print("Slider found")
                # Move slider
                slider.fill("150") # Simulate input
                # Take screenshot of resized logo
                page.screenshot(path="verification/sponsors_resize.png")
                print("Sponsors screenshot taken")
            else:
                print("Slider NOT found (maybe not logged in as admin?)")
                # To test slider, I need to be admin.
                # Perform Login
                page.locator("text=Admin Login").first.click()
                page.fill("input[name='userid']", "adminwebsite")
                page.fill("input[name='password']", "4dm1nw3bs1t3")
                page.click("button:has-text('Login')")
                time.sleep(2)
                print("Logged in as Admin")

                page.goto("http://localhost:5000", wait_until="domcontentloaded")
                page.locator("#sponsors").scroll_into_view_if_needed()
                slider = page.locator(".custom-range-slider").first
                if slider.count() > 0:
                     slider.fill("150")
                     page.screenshot(path="verification/sponsors_resize_admin.png")
                     print("Sponsors Admin screenshot taken")
                else:
                    print("Slider still not found even after login")
        except Exception as e:
            print(f"Sponsors check failed: {e}")

        browser.close()

if __name__ == "__main__":
    verify_changes()
