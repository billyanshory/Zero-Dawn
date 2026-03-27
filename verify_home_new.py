from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:5000')
        page.wait_for_timeout(3000)

        # Take full page screenshot
        page.screenshot(path='/home/jules/verification/screenshots/home_main_updated.png', full_page=True)

        browser.close()

if __name__ == '__main__':
    verify()
