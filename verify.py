from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:5000/antrean")
        page.click("button[onclick='toggleTheme()']")
        page.screenshot(path="verification.png")
        browser.close()

if __name__ == "__main__":
    verify()
