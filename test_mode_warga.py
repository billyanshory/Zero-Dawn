from playwright.sync_api import sync_playwright
import time

def test_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading /...")
        page.goto("http://localhost:5019/")

        print("Opening login modal...")
        page.evaluate("openLogin('admin')")
        page.wait_for_selector("#loginModal", state="visible")

        print("Filling login form...")
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "admin123")
        page.click("button[type=submit]")

        print("Waiting for dashboard redirect...")
        page.wait_for_url("**/dashboard")
        print("Redirected to dashboard successfully!")

        page.screenshot(path="dashboard_new.png")

        print("Clicking 'Mode Warga'...")
        page.click("a:has-text('Mode Warga')")

        print("Waiting for redirect to home...")
        page.wait_for_url("http://localhost:5019/")

        print("Successfully returned to home page!")
        page.screenshot(path="home_after_mode_warga_new.png")
        browser.close()

test_flow()
