"""End-to-end smoke test using Playwright."""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"

ROUTES = [
    "/",
]


async def test_page(page, route: str):
    """Test a single route and collect console errors."""
    errors = []
    warnings = []

    def handle_console(msg):
        if msg.type == "error":
            errors.append(msg.text)
        elif msg.type == "warning":
            warnings.append(msg.text)

    page.on("console", handle_console)

    # Collect failed network requests
    failed_requests = []

    def handle_request_failed(req):
        failed_requests.append(f"{req.method} {req.url} -> {req.failure['error_text'] if req.failure else 'unknown'}")

    page.on("requestfailed", handle_request_failed)

    try:
        await page.goto(f"{BASE_URL}{route}", wait_until="networkidle", timeout=15000)
        # Wait a bit for JS to settle
        await asyncio.sleep(2)
    except Exception as e:
        return {"route": route, "ok": False, "nav_error": str(e), "errors": [], "warnings": [], "failed": []}

    return {
        "route": route,
        "ok": True,
        "nav_error": None,
        "errors": errors,
        "warnings": warnings,
        "failed": failed_requests,
    }


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for route in ROUTES:
            print(f"Testing {route} ...")
            result = await test_page(page, route)
            results.append(result)

        await browser.close()

    # Report
    print("\n" + "=" * 60)
    print("SMOKE TEST REPORT")
    print("=" * 60)

    has_issues = False
    for r in results:
        status = "OK" if r["ok"] else "NAV_FAIL"
        issues = len(r["errors"]) + len(r["failed"])
        if not r["ok"] or issues > 0:
            has_issues = True
            print(f"\n[{status}] {r['route']}")
            if r["nav_error"]:
                print(f"  Navigation Error: {r['nav_error']}")
            for e in r["errors"]:
                print(f"  Console Error: {e}")
            for f in r["failed"]:
                print(f"  Network Failed: {f}")
            for w in r["warnings"]:
                print(f"  Console Warning: {w}")
        else:
            print(f"  [OK] {r['route']}")

    if not has_issues:
        print("\nAll routes loaded without errors!")
    else:
        print("\nIssues found — see details above.")


if __name__ == "__main__":
    asyncio.run(main())
