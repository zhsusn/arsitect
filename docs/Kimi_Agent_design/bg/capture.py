
import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 794, "height": 1123})

        await page.goto("file:///mnt/agents/output/bg/cover.html")
        await page.screenshot(path="/mnt/agents/output/bg/cover_bg.png", clip={"x": 0, "y": 0, "width": 794, "height": 1123}, scale="css")

        await page.goto("file:///mnt/agents/output/bg/back.html")
        await page.screenshot(path="/mnt/agents/output/bg/backcover_bg.png", clip={"x": 0, "y": 0, "width": 794, "height": 1123}, scale="css")

        await browser.close()

asyncio.run(capture())
