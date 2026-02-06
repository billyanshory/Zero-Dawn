import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:5000")
        page.locator("button[title='Ganti Tema']").click()
        page.locator("button:has-text('Dark')").click()
        time.sleep(1)
        page.screenshot(path="verification/verification_dark_home.png")
        browser.close()

if __name__ == "__main__":
    run()
