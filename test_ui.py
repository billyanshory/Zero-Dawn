import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Dashboard TU
        await page.goto('http://127.0.0.1:5000/ramadhan')
        content_tu = await page.content()
        assert "Surat Otomatis" in content_tu
        assert "Verifikasi PMB" in content_tu
        assert "Arsip Digital" in content_tu
        assert "Verifikasi SPP" in content_tu
        assert "Jadwal Kuliah" in content_tu
        assert "Kelola Sivitas" in content_tu

        print("TU Dashboard verified!")

        # Dashboard Dosen
        await page.goto('http://127.0.0.1:5000/dosen')
        content_dosen = await page.content()
        assert "MENU UTAMA" in content_dosen
        assert "Persetujuan KRS" in content_dosen
        assert "Input Nilai" in content_dosen
        assert "Mahasiswa Wali" in content_dosen
        assert "Jadwal Mengajar" in content_dosen
        assert "Presensi Kelas" in content_dosen
        assert "Profil Dosen" in content_dosen

        print("Dosen Dashboard verified!")

        # Tracer form
        await page.goto('http://127.0.0.1:5000/ramadhan')
        content_tracer = await page.content()
        assert "modal-tracer-form" in content_tracer
        assert "Nomor Pokok Mahasiswa (NPM)" in content_tracer

        print("Tracer form verified!")

        # Modal developer
        assert "flex flex-col h-full max-h-screen" in content_tracer

        print("Modal developer UI elements verified!")

        await browser.close()

asyncio.run(main())
