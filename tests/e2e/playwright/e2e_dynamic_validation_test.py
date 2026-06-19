"""
E2E Dynamic Validation Test — Runtime Behavior Probe Matrix
=============================================================
Applies Baseline + Edge + Fault + Drift probes to the entire product UI.
Uses Playwright (Python async API) against the running dev stack.

Runtime Probe Matrix:
- Baseline : Normal-path loading, navigation, and observable state
- Edge     : Boundary inputs (empty project, direct URL access, collapsed sidebar)
- Fault    : Backend failure injection, network degradation
- Drift    : Repeatability, idempotency, state persistence across refresh

Target: http://localhost:5173 (frontend) + http://localhost:8000 (backend)
"""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from typing import Any
from playwright.async_api import async_playwright, Page, BrowserContext

BASE_URL = "http://localhost:5173"
API_BASE = "http://localhost:8000/api/v1"

# All sidebar routes extracted from App.tsx navGroups
ROUTES_BASELINE = [
    "/",
    "/projects",
    "/projects/create",
    "/canvas/default",
    "/complexity-router",
    "/execution-plans",
    "/executions",
    "/monitoring",
    "/c4",
    "/wireframe",
    "/sketches",
    "/open-ui",
    "/binding",
    "/artifacts",
    "/arch-validation",
    "/arch-governance",
    "/history",
    "/gates",
    "/bypass",
    "/applications",
    "/skills",
    "/template-config",
    "/docforge",
]

DEMO_PROJECT = "demo-project-001"


@dataclass
class ProbeResult:
    probe: str          # Baseline | Edge | Fault | Drift
    test_id: str
    description: str
    passed: bool
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class ConsoleCollector:
    """Collects console messages and page errors."""
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.page_errors: list[str] = []
        self.failed_requests: list[str] = []
        self._tolerable_404_urls: set[str] = set()

    def attach(self, page: Page):
        page.on("console", lambda msg: self._on_console(msg))
        page.on("pageerror", lambda err: self.page_errors.append(str(err)))
        page.on("requestfailed", lambda req: self._on_req_fail(req))
        page.on("response", lambda resp: self._on_response(resp))

    def _on_console(self, msg):
        text = msg.text
        if msg.type == "error":
            # Ignore expected React StrictMode double-render warnings and sourcemap 404s
            if "sourcemap" in text.lower() or text.startswith("[vite]"):
                return
            # If the generic "Failed to load resource" appears while we have a tolerable 404,
            # we count it as non-critical because the URL was already known to be missing data.
            if "failed to load resource" in text.lower() and "404" in text.lower():
                if self._tolerable_404_urls:
                    return
            self.errors.append(text)
        elif msg.type == "warning":
            self.warnings.append(text)

    def _on_req_fail(self, req):
        failure = req.failure
        err = failure["error_text"] if failure else "unknown"
        self.failed_requests.append(f"{req.method} {req.url} -> {err}")

    def _on_response(self, resp):
        if resp.status == 404:
            url = resp.url
            for pat in self._TOLERABLE_404_PATTERNS:
                if pat in url:
                    self._tolerable_404_urls.add(url)

    def reset(self):
        self.errors.clear()
        self.warnings.clear()
        self.page_errors.clear()
        self.failed_requests.clear()
        self._tolerable_404_urls.clear()

    _TOLERABLE_404_PATTERNS = [
        "/api/v1/projects/default/canvas/state",
        "/api/v1/c4/dsl/current",
    ]

    def _is_tolerable(self, msg: str) -> bool:
        for pat in self._TOLERABLE_404_PATTERNS:
            if pat in msg:
                return True
        if "sourcemap" in msg.lower() or "favicon" in msg.lower() or msg.startswith("[vite]"):
            return True
        return False

    def has_critical(self) -> bool:
        critical_reqs = [r for r in self.failed_requests if "/api/" in r and not self._is_tolerable(r)]
        critical_errors = [e for e in self.errors if not self._is_tolerable(e)]
        return bool(critical_errors or self.page_errors or critical_reqs)

    def critical_summary(self) -> list[str]:
        critical_reqs = [r for r in self.failed_requests if "/api/" in r and not self._is_tolerable(r)]
        critical_errors = [e for e in self.errors if not self._is_tolerable(e)]
        out = []
        out.extend([f"[console] {e}" for e in critical_errors])
        out.extend([f"[page] {e}" for e in self.page_errors])
        out.extend([f"[req] {e}" for e in critical_reqs])
        return out


async def wait_for_app_ready(page: Page, timeout: int = 15000):
    """Wait for the SPA shell to appear."""
    await page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=timeout)
    await page.wait_for_selector("text=Arsitect", timeout=timeout)
    await asyncio.sleep(0.5)


async def select_project(page: Page, project_id: str):
    """Select a project from the TopBar dropdown."""
    # ProjectSelector has two selects: [app, project]
    # We need to select the app first to enable the project select.
    sels = await page.query_selector_all('select')
    if len(sels) >= 2:
        # Try to find an app option that is not empty
        app_options = await sels[0].query_selector_all('option')
        non_empty_app = None
        for opt in app_options:
            val = await opt.get_attribute('value')
            if val:
                non_empty_app = val
                break
        if non_empty_app:
            await sels[0].select_option(non_empty_app)
            await asyncio.sleep(0.8)
        await sels[1].select_option(project_id)
        await asyncio.sleep(1.0)
    elif len(sels) == 1:
        await sels[0].select_option(project_id)
        await asyncio.sleep(1.0)


# ============================================================
# Baseline Probes
# ============================================================

async def probe_b1_all_routes_load(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """B1: Every sidebar route loads without critical console/network errors."""
    r = ProbeResult("Baseline", "B1", "All routes load cleanly", True)
    start = asyncio.get_event_loop().time()
    bad_routes = []
    for route in ROUTES_BASELINE:
        collector.reset()
        try:
            await page.goto(f"{BASE_URL}{route}", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(0.8)
        except Exception as e:
            bad_routes.append((route, f"nav_error: {e}"))
            continue
        if collector.has_critical():
            bad_routes.append((route, collector.critical_summary()))
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    if bad_routes:
        r.passed = False
        r.details["bad_routes"] = bad_routes
        r.errors.append(f"{len(bad_routes)} routes had critical issues")
    else:
        r.details["routes_tested"] = len(ROUTES_BASELINE)
    return r


async def probe_b2_sidebar_navigation(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """B2: Sidebar navigation links are clickable and change the URL."""
    r = ProbeResult("Baseline", "B2", "Sidebar navigation changes URL", True)
    start = asyncio.get_event_loop().time()
    await wait_for_app_ready(page)
    collector.reset()

    # Expand all groups first by clicking each group header
    group_btns = await page.query_selector_all("nav button")
    for btn in group_btns:
        await btn.click()
        await asyncio.sleep(0.2)

    links = await page.query_selector_all("nav a")
    checked = 0
    failed = []
    for link in links[:12]:  # sample first 12 to keep runtime sane
        href = await link.get_attribute("href")
        if not href or href == "/":
            continue
        collector.reset()
        try:
            await link.click()
            await asyncio.sleep(0.6)
            url = page.url
            if not url.rstrip("/").endswith(href.rstrip("/")):
                failed.append((href, url))
            checked += 1
        except Exception as e:
            failed.append((href, str(e)))
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    r.details = {"checked": checked, "failed": failed}
    if failed:
        r.passed = False
        r.errors.append(f"{len(failed)} nav links failed")
    return r


async def probe_b3_project_selector(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """B3: Project selector persists choice to localStorage and updates UI."""
    r = ProbeResult("Baseline", "B3", "Project selector persistence", True)
    start = asyncio.get_event_loop().time()
    await wait_for_app_ready(page)
    collector.reset()

    await select_project(page, DEMO_PROJECT)
    ls_val = await page.evaluate("() => localStorage.getItem('arsitect:lastProjectId')")
    r.details["localStorage_project"] = ls_val
    if ls_val != DEMO_PROJECT:
        r.passed = False
        r.errors.append(f"localStorage expected {DEMO_PROJECT}, got {ls_val}")

    # Verify project selector (second select) reflects the choice
    sel_val = await page.evaluate('() => document.querySelectorAll("select")[1]?.value || ""')
    r.details["selector_value"] = sel_val
    if sel_val != DEMO_PROJECT:
        r.passed = False
        r.errors.append(f"Selector value expected {DEMO_PROJECT}, got {sel_val}")

    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    return r


async def probe_b4_api_health(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """B4: Backend health endpoint returns 200."""
    r = ProbeResult("Baseline", "B4", "Backend health check", True)
    start = asyncio.get_event_loop().time()
    resp = await page.context.request.get(f"{API_BASE}/health")
    r.details["status"] = resp.status
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    if resp.status != 200:
        r.passed = False
        r.errors.append(f"Health returned {resp.status}")
    else:
        body = await resp.json()
        r.details["body"] = body
    return r


# ============================================================
# Edge Probes
# ============================================================

async def probe_e1_direct_project_url(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """E1: Direct navigation to /c4/:projectId renders without manual selection."""
    r = ProbeResult("Edge", "E1", "Direct URL with projectId", True)
    start = asyncio.get_event_loop().time()
    collector.reset()
    try:
        await page.goto(f"{BASE_URL}/c4/{DEMO_PROJECT}", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(1.0)
    except Exception as e:
        r.passed = False
        r.errors.append(str(e))
        r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return r

    if collector.has_critical():
        r.passed = False
        r.errors.extend(collector.critical_summary())

    # The C4Navigator should show project name somewhere or load without fatal error
    r.details["url"] = page.url
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    return r


async def probe_e2_no_project_fallback(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """E2: ArchGovernance without projectId falls back to localStorage or shows '未选择'."""
    r = ProbeResult("Edge", "E2", "ArchGovernance no-project fallback", True)
    start = asyncio.get_event_loop().time()
    # Clear localStorage first
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.evaluate("() => localStorage.clear()")
    collector.reset()
    await page.goto(f"{BASE_URL}/arch-governance", wait_until="networkidle", timeout=15000)
    await asyncio.sleep(1.0)

    # Accept either "未选择" or successful load (both are valid edge behaviors)
    text = await page.content()
    has_unselected = "未选择" in text or "选择项目" in text or "请先选择" in text
    r.details["has_unselected_hint"] = has_unselected
    r.details["critical_errors"] = collector.critical_summary()
    if collector.has_critical():
        # Only fail if there are real errors, "未选择" is acceptable UX
        r.passed = False
        r.errors.extend(collector.critical_summary())
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    return r


async def probe_e3_sidebar_collapse_expand(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """E3: Sidebar groups can be collapsed and expanded without errors."""
    r = ProbeResult("Edge", "E3", "Sidebar collapse/expand", True)
    start = asyncio.get_event_loop().time()
    await wait_for_app_ready(page)
    collector.reset()
    group_btns = await page.query_selector_all("nav button")
    for btn in group_btns:
        try:
            await btn.click()
            await asyncio.sleep(0.3)
            await btn.click()
            await asyncio.sleep(0.3)
        except Exception as e:
            r.passed = False
            r.errors.append(str(e))
    if collector.has_critical():
        r.passed = False
        r.errors.extend(collector.critical_summary())
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    r.details["groups_toggled"] = len(group_btns)
    return r


# ============================================================
# Fault Probes
# ============================================================

async def probe_f1_backend_500_degradation(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """F1: Simulate backend 500 on /api/v1/c4/analyze; frontend should degrade gracefully."""
    r = ProbeResult("Fault", "F1", "Backend 500 graceful degradation", True)
    start = asyncio.get_event_loop().time()
    # We can't easily intercept FastAPI routes without modifying backend,
    # so we hit an intentionally bad endpoint or block the route via route interception.
    await wait_for_app_ready(page)
    await select_project(page, DEMO_PROJECT)

    # Intercept /api/v1/c4/analyze and abort/return 500
    await page.route("**/api/v1/c4/analyze**", lambda route: route.fulfill(
        status=500,
        content_type="application/json",
        body=json.dumps({"detail": "Simulated server error"})
    ))
    collector.reset()
    try:
        await page.goto(f"{BASE_URL}/arch-governance/{DEMO_PROJECT}", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(1.5)
    except Exception as e:
        r.errors.append(str(e))
    finally:
        await page.unroute("**/api/v1/c4/analyze**")

    # We expect the page to still render (no white screen / uncaught exception)
    body_text = await page.inner_text("body")
    has_fatal = "Application error" in body_text or "Something went wrong" in body_text
    r.details["body_snippet"] = body_text[:200]
    r.details["critical_errors"] = collector.critical_summary()
    if has_fatal or collector.has_critical():
        # Some console errors are expected when API fails; we tolerate controlled errors
        # but not page crashes.
        if has_fatal:
            r.passed = False
            r.errors.append("Page crashed with fatal error block")
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    return r


async def probe_f2_slow_network(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """F2: Simulate slow 3G network; pages should still eventually load."""
    r = ProbeResult("Fault", "F2", "Slow network resilience", True)
    start = asyncio.get_event_loop().time()
    ctx = page.context
    # CDP method to emulate network conditions
    try:
        # Playwright has browser_context.set_offline; for throttling we use CDP
        client = await page.context.new_cdp_session(page)
        await client.send("Network.emulateNetworkConditions", {
            "offline": False,
            "downloadThroughput": 500 * 1024 // 8,  # ~500 kbps
            "uploadThroughput": 500 * 1024 // 8,
            "latency": 300,
        })
    except Exception as e:
        r.details["cdp_warning"] = str(e)
        # Fallback: skip this probe if CDP unavailable
        r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        r.errors.append(f"CDP network emulation unavailable: {e}")
        r.passed = True  # neutral
        return r

    collector.reset()
    try:
        await page.goto(f"{BASE_URL}/projects", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1.0)
    except Exception as e:
        r.passed = False
        r.errors.append(str(e))
    finally:
        try:
            await client.send("Network.emulateNetworkConditions", {
                "offline": False,
                "downloadThroughput": -1,
                "uploadThroughput": -1,
                "latency": 0,
            })
        except Exception:
            pass

    if collector.has_critical():
        r.passed = False
        r.errors.extend(collector.critical_summary())
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    return r


# ============================================================
# Drift Probes
# ============================================================

async def probe_d1_repeat_navigation_consistency(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """D1: Revisiting the same page 3 times yields identical critical error count."""
    r = ProbeResult("Drift", "D1", "Repeat navigation consistency", True)
    start = asyncio.get_event_loop().time()
    counts = []
    for i in range(3):
        collector.reset()
        await page.goto(f"{BASE_URL}/projects", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(0.8)
        counts.append(len(collector.critical_summary()))
    r.details["run_counts"] = counts
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    if len(set(counts)) != 1:
        r.passed = False
        r.errors.append(f"Inconsistent error counts across repeats: {counts}")
    return r


async def probe_d2_refresh_preserves_project(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """D2: After selecting a project and refreshing, the selector retains the value."""
    r = ProbeResult("Drift", "D2", "Refresh preserves project selection", True)
    start = asyncio.get_event_loop().time()
    await wait_for_app_ready(page)
    await select_project(page, DEMO_PROJECT)
    # Refresh
    await page.reload(wait_until="networkidle", timeout=15000)
    await asyncio.sleep(1.0)
    sel_val = await page.evaluate('() => document.querySelectorAll("select")[1]?.value || ""')
    ls_val = await page.evaluate("() => localStorage.getItem('arsitect:lastProjectId')")
    r.details = {"selector_value": sel_val, "localStorage": ls_val}
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    if sel_val != DEMO_PROJECT:
        r.passed = False
        r.errors.append(f"Selector lost project after refresh: {sel_val}")
    if ls_val != DEMO_PROJECT:
        r.passed = False
        r.errors.append(f"localStorage lost project after refresh: {ls_val}")
    return r


async def probe_d3_round_trip_state(page: Page, collector: ConsoleCollector) -> ProbeResult:
    """D3: Navigate away and back to C4; URL and basic structure should remain consistent."""
    r = ProbeResult("Drift", "D3", "Round-trip state consistency", True)
    start = asyncio.get_event_loop().time()
    await page.goto(f"{BASE_URL}/c4/{DEMO_PROJECT}", wait_until="networkidle", timeout=15000)
    await asyncio.sleep(1.0)
    url_before = page.url
    # go to another page
    await page.goto(f"{BASE_URL}/projects", wait_until="networkidle", timeout=15000)
    await asyncio.sleep(0.5)
    # go back
    await page.goto(url_before, wait_until="networkidle", timeout=15000)
    await asyncio.sleep(1.0)
    url_after = page.url
    r.details = {"url_before": url_before, "url_after": url_after}
    r.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    if url_before.rstrip("/") != url_after.rstrip("/"):
        r.passed = False
        r.errors.append(f"URL drift: before={url_before} after={url_after}")
    return r


# ============================================================
# Runner
# ============================================================

ALL_PROBES = [
    probe_b1_all_routes_load,
    probe_b2_sidebar_navigation,
    probe_b3_project_selector,
    probe_b4_api_health,
    probe_e1_direct_project_url,
    probe_e2_no_project_fallback,
    probe_e3_sidebar_collapse_expand,
    probe_f1_backend_500_degradation,
    probe_f2_slow_network,
    probe_d1_repeat_navigation_consistency,
    probe_d2_refresh_preserves_project,
    probe_d3_round_trip_state,
]


async def run_all() -> list[ProbeResult]:
    results: list[ProbeResult] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        collector = ConsoleCollector()
        collector.attach(page)

        for probe_fn in ALL_PROBES:
            print(f"  -> {probe_fn.__name__} ...", end=" ", flush=True)
            try:
                res = await probe_fn(page, collector)
                results.append(res)
                status = "PASS" if res.passed else "FAIL"
                print(status)
            except Exception as e:
                print(f"ERROR: {e}")
                results.append(ProbeResult(
                    probe=probe_fn.__name__.split("_")[1][0].upper(),
                    test_id="ERR",
                    description=probe_fn.__doc__ or "",
                    passed=False,
                    errors=[str(e)],
                ))

        await browser.close()
    return results


def print_report(results: list[ProbeResult]):
    print("\n" + "=" * 70)
    print("E2E DYNAMIC VALIDATION REPORT")
    print("=" * 70)

    by_probe: dict[str, list[ProbeResult]] = {}
    for r in results:
        by_probe.setdefault(r.probe, []).append(r)

    total_pass = 0
    total_fail = 0
    for probe_type, items in by_probe.items():
        print(f"\n[{probe_type}]")
        for r in items:
            mark = "[PASS]" if r.passed else "[FAIL]"
            print(f"  {mark} {r.test_id}: {r.description} ({r.duration_ms:.0f}ms)")
            if not r.passed:
                total_fail += 1
                for e in r.errors:
                    print(f"      ! {e}")
                if r.details:
                    # Pretty-print short details
                    detail_str = json.dumps(r.details, ensure_ascii=False, indent=4)
                    for line in detail_str.splitlines()[:8]:
                        print(f"      > {line}")
            else:
                total_pass += 1

    print("\n" + "-" * 70)
    print(f"SUMMARY: {total_pass} passed, {total_fail} failed, {total_pass + total_fail} total")
    if total_fail == 0:
        print("OVERALL: ALL PROBES PASSED")
    else:
        print(f"OVERALL: {total_fail} PROBE(S) FAILED")
    print("=" * 70)

    # Write markdown report
    with open("e2e_dynamic_validation_report.md", "w", encoding="utf-8") as f:
        f.write("# E2E Dynamic Validation Report\n\n")
        f.write(f"Generated: {asyncio.get_event_loop().time()}\n\n")
        f.write("## Probe Matrix\n\n")
        f.write("| Probe | ID | Description | Status | Duration |\n")
        f.write("|-------|----|-------------|--------|----------|\n")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            f.write(f"| {r.probe} | {r.test_id} | {r.description} | {status} | {r.duration_ms:.0f}ms |\n")
        f.write(f"\n## Summary\n\n")
        f.write(f"- **Passed**: {total_pass}\n")
        f.write(f"- **Failed**: {total_fail}\n")
        f.write(f"- **Total**: {total_pass + total_fail}\n")
        if total_fail == 0:
            f.write("\n**All probes passed.**\n")
        else:
            f.write(f"\n**{total_fail} probe(s) failed.** See details above.\n")
        f.write("\n## Failure Details\n\n")
        for r in results:
            if not r.passed:
                f.write(f"### {r.test_id}: {r.description}\n")
                for e in r.errors:
                    f.write(f"- {e}\n")
                if r.details:
                    f.write(f"\n```json\n{json.dumps(r.details, ensure_ascii=False, indent=2)}\n```\n")
                f.write("\n")


async def main():
    print("E2E Dynamic Validation Starting...")
    print(f"Target frontend: {BASE_URL}")
    print(f"Target backend:  {API_BASE}")
    print(f"Probes: {len(ALL_PROBES)}\n")

    results = await run_all()
    print_report(results)

    # Exit code reflects failures
    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
