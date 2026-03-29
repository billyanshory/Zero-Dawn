from playwright.sync_api import sync_playwright

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/videos")
        page = context.new_page()
        try:
            page.goto("http://127.0.0.1:5000/")
            page.wait_for_timeout(1000)

            # Click Tracer Study box
            page.evaluate("openModal('modal-tracer-study')")
            page.wait_for_timeout(1000)

            # Click Isi Kuesioner
            page.evaluate("openModal('modal-tracer-form')")
            page.wait_for_timeout(1000)

            # Fill form
            page.fill("input[name='nama_lengkap']", "John Doe", force=True)
            page.fill("input[name='npm']", "123456", force=True)
            page.fill("input[name='tahun_lulus']", "2023", force=True)
            page.select_option("select[name='program_studi']", "S1 Manajemen", force=True)
            page.select_option("select[name='status_pekerjaan']", "Bekerja (Full-time)", force=True)
            page.fill("input[name='nama_perusahaan']", "PT Maju Jaya", force=True)
            page.fill("input[name='jabatan']", "Manager", force=True)
            page.fill("input[name='kontak']", "08123456789", force=True)

            page.wait_for_timeout(500)

            # Handle alert dialog to avoid stopping script
            page.once("dialog", lambda dialog: dialog.accept())

            # Submit form
            page.evaluate('document.querySelector("form[action=\'/api/tracer/submit\']").submit()')
            page.wait_for_timeout(2000)

            # Open Cek Alumni via tu portal
            page.goto("http://127.0.0.1:5000/ramadhan")
            page.wait_for_timeout(1000)

            page.evaluate("openModal('modal-cek-alumni')")
            page.wait_for_timeout(1000)

            page.screenshot(path="/home/jules/verification/screenshots/verification.png")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    run_test()
