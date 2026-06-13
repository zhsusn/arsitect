"""Test sketch import from requirements."""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"


async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        page.on("console", lambda msg: errors.append(f"[console] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: errors.append(f"[page] {err}"))

        # Go to sketches page
        await page.goto(f"{BASE_URL}/sketches", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(1)

        # Wait for project selector to load and select demo project
        selector = await page.query_selector('select')
        if selector:
            await selector.select_option('demo-project-001')
            await asyncio.sleep(1.5)

        # Click import button
        import_btn = await page.query_selector('text=从需求导入')
        if import_btn:
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            await import_btn.click()
            await asyncio.sleep(2)
        else:
            errors.append("Import button not found")

        await browser.close()

    print("=" * 50)
    print("SKETCH IMPORT TEST")
    print("=" * 50)
    if errors:
        print(f"Found {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("No errors detected!")


if __name__ == "__main__":
    asyncio.run(main())
