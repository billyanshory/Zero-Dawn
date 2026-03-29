import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Beranda Tracer form
        await page.goto('http://127.0.0.1:5000/')
        content_tracer = await page.content()
        assert "modal-tracer-form" in content_tracer
        assert "Nomor Pokok Mahasiswa (NPM)" in content_tracer

        print("Tracer form verified in Beranda!")

        # Modal developer
        assert "flex flex-col h-full max-h-screen" in content_tracer

        print("Modal developer UI elements verified!")

        await browser.close()

asyncio.run(main())
