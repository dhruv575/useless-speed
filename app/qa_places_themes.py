"""Headless place-search and time-of-day checks; BASE_URL defaults to localhost."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8788").rstrip("/")
OUT = Path(__file__).parent / "test-output"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1512, "height": 982}, device_scale_factor=1)
    errors, checks, colors = [], [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_function('!document.querySelector(".configuration").disabled')
    page.wait_for_timeout(1600)
    page.locator(".maplibregl-canvas").evaluate('e => e.dataset.testIdentity = "original"')
    for name in ["Morning", "Midday", "Evening", "Night"]:
        page.get_by_role("radio", name=re.compile("^" + name)).check()
        page.wait_for_timeout(250)
        assert page.locator("html").get_attribute("data-theme") == name.lower()
        colors.append(page.locator(".sidebar").evaluate("e => getComputedStyle(e).backgroundColor"))
        assert page.locator(".maplibregl-canvas").get_attribute("data-test-identity") == "original"
        page.screenshot(path=str(OUT / f"theme-{name.lower()}.png"), full_page=True)
    assert len(set(colors)) == 4
    checks.append("four distinct themes without recreating the map")

    for label, query, expected in [
        ("Starting point", "Tartine Bakery", "Tartine Bakery"),
        ("Destination", "Dolores Park", "Mission Dolores Park"),
    ]:
        field = page.get_by_role("combobox", name=label)
        field.fill(query)
        page.locator(".search-results [role=option]").first.wait_for(timeout=15000)
        assert page.locator(".search-results strong").first.inner_text() == expected
        if label == "Destination":
            page.screenshot(path=str(OUT / "theme-night-search.png"))
        field.press("ArrowDown")
        field.press("Enter")
        assert field.input_value() == expected
    checks.append("place names select by keyboard and keep their original casing")
    page.get_by_role("button", name="Simulate", exact=True).click()
    page.get_by_role("button", name="Pause simulation").wait_for(timeout=45000)
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Pause simulation").click()
    assert page.locator(".car-marker").count() == 2
    assert all(s.endswith("min") for s in page.locator(".trip-time>output").all_text_contents())
    page.screenshot(path=str(OUT / "theme-night-route.png"))
    page.get_by_role("button", name="Resume simulation").click()
    page.wait_for_function('document.querySelector(".metrics").dataset.state === "finished"', timeout=45000)
    checks.append("a route between named places runs to completion in night mode")

    selected = page.get_by_role("combobox").evaluate_all("els => els.map(e => e.value)")
    for name in ["Morning", "Night", "Evening", "Midday"]:
        page.get_by_role("radio", name=re.compile("^" + name)).check()
        assert page.get_by_role("combobox").evaluate_all("els => els.map(e => e.value)") == selected
        assert page.locator(".map-endpoint").count() == 2
        assert page.locator(".maplibregl-canvas").get_attribute("data-test-identity") == "original"
    checks.append("theme switches retain selected places and map pins")

    field = page.get_by_role("combobox", name="Starting point")
    field.fill("100 Van Ness Avenue")
    page.locator(".search-results [role=option]").first.wait_for(timeout=15000)
    assert page.locator(".search-results strong").first.inner_text() == "100 van ness ave"
    field.press("Enter")
    field.fill("unlikelyplacexqz")
    page.get_by_text("No matching place or address.", exact=False).wait_for()
    assert page.get_by_role("button", name="Simulate", exact=True).is_disabled()
    field.fill("x")
    field.fill("Ferry Building")
    page.locator(".search-results [role=option]").first.wait_for(timeout=15000)
    assert "Ferry Building" in page.locator(".search-results strong").first.inner_text()
    field.press("Enter")
    checks.append("street addresses, empty search and recovery remain functional")

    page.get_by_role("radio", name=re.compile("^Night")).check()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator(".address-box input").evaluate_all('els => els.every(e => e.autocapitalize === "none")')
    page.screenshot(path=str(OUT / "theme-night-mobile.png"), full_page=True)
    checks.append("mobile dark theme fits and autocapitalization stays off")
    browser.close()
    report = {"base_url": BASE, "checks": checks, "errors": errors}
    (OUT / "places-themes-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert not errors, errors
