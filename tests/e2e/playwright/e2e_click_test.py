"""Deep click-through test using Playwright."""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"

NAV_LINKS = [
    ("仪表盘", "/dashboard"),
    ("画布", "/canvas"),
    ("审批中心", "/gates"),
    ("产物", "/artifacts"),
    ("项目", "/projects"),
    ("执行计划", "/execution-plans"),
    ("模板", "/templates"),
    ("技能", "/skills"),
    ("监控", "/monitoring"),
    ("C4", "/c4"),
    ("线框图", "/wireframes"),
    ("草图", "/sketches"),
    ("用户故事", "/user-stories"),
]


async def main():
    errors_all = []
    current_route = "/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        def handle_console(msg):
            if msg.type == "error":
                url = msg.location.get("url", "") if msg.location else ""
                errors_all.append(f"[console][{current_route}] {msg.text} | url={url}")

        page.on("console", handle_console)

        def handle_page_error(err):
            errors_all.append(f"[page-error][{current_route}] {err}")

        page.on("pageerror", handle_page_error)

        def handle_req_fail(req):
            errors_all.append(f"[network][{current_route}] {req.method} {req.url} -> {req.failure['error_text'] if req.failure else 'unknown'}")

        page.on("requestfailed", handle_req_fail)

        # Load home
        await page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
        await asyncio.sleep(1)

        for label, route in NAV_LINKS:
            current_route = route
            print(f"Navigating to {label} ({route}) ...")
            try:
                link = await page.query_selector(f'a[href="{route}"]')
                if link:
                    await link.click()
                else:
                    await page.goto(f"{BASE_URL}{route}", wait_until="networkidle", timeout=10000)
                await asyncio.sleep(1.5)
            except Exception as e:
                errors_all.append(f"[nav-fail][{route}] {e}")

        await browser.close()

    print("\n" + "=" * 60)
    print("CLICK-THROUGH TEST REPORT")
    print("=" * 60)
    if errors_all:
        print(f"\nFound {len(errors_all)} error(s):")
        for e in errors_all:
            print(f"  - {e}")
    else:
        print("\nNo console or navigation errors detected!")


if __name__ == "__main__":
    asyncio.run(main())
