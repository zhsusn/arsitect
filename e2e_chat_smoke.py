import asyncio
from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto("http://localhost:5173/cli")
        await page.wait_for_timeout(1500)
        await page.screenshot(path="D:/srccode/arsitect/test-results/chat_home.png")

        # Type a message and send from home page using Enter
        await page.fill('textarea', 'hello')
        await page.press('textarea', 'Enter')

        # Wait for navigation to session page and connection
        await page.wait_for_selector('text=已连接', timeout=10000)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="D:/srccode/arsitect/test-results/chat_session_connected.png")

        # Send another message in session page
        await page.fill('textarea', 'test message')
        await page.press('textarea', 'Enter')
        await page.wait_for_timeout(6000)
        await page.screenshot(path="D:/srccode/arsitect/test-results/chat_session_replied.png")

        await browser.close()
        print("screenshots saved")


if __name__ == "__main__":
    asyncio.run(main())
