import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright

def main():
    # Start the Flask app
    process = subprocess.Popen(["python3", "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"])
    time.sleep(3) # Wait for startup

    try:
        req = urllib.request.Request("http://127.0.0.1:5000/ramadhan")
        try:
            res = urllib.request.urlopen(req)
            if res.status == 200:
                print("SUCCESS: /ramadhan returned 200 OK")
            else:
                print(f"FAILED: /ramadhan returned {res.status}")
        except Exception as e:
            print(f"FAILED: /ramadhan Error: {e}")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://127.0.0.1:5000/ramadhan")

            # Check if elements exist instead of crashing if they don't, for robustness
            buttons = [
                ("Pabrik Surat Otomatis", "modal-pabrik-surat"),
                ("Verifikasi PMB Digital", "modal-verifikasi-pmb"),
                ("Laci Arsip Anti Rayap", "modal-laci-arsip"),
                ("Verifikasi Pembayaran Uang", "modal-verifikasi-pembayaran"),
                ("Kelola Jadwal", "modal-kelola-jadwal"),
                ("Manajemen Sivitas Akademika", "modal-manajemen-sivitas")
            ]

            for btn_text, modal_id in buttons:
                print(f"Testing {btn_text}...")
                page.locator(f"button:has-text('{btn_text}')").click(force=True)
                time.sleep(0.5)
                # Check visibility
                is_visible = page.locator(f"#{modal_id}").is_visible()
                print(f" Modal {modal_id} visible: {is_visible}")

                # Close modal
                page.locator(f"#{modal_id} button.text-gray-400").click(force=True)
                time.sleep(0.5)

            browser.close()

    finally:
        process.terminate()

if __name__ == "__main__":
    main()
