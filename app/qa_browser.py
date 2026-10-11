"""Headless checks for the minimal sidebar and live comparison."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / 'test-output'
OUT.mkdir(exist_ok=True)
checks, errors = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True, args=['--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width':1512,'height':982}, device_scale_factor=1)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.goto('http://127.0.0.1:8788/', wait_until='domcontentloaded')
    page.wait_for_function("!document.querySelector('.configuration').disabled", timeout=60000)
    page.wait_for_timeout(1500)
    assert page.get_by_placeholder('Starting point').input_value() == ''
    assert page.get_by_placeholder('Destination').input_value() == ''
    assert page.get_by_role('slider').input_value() == '20'
    assert page.get_by_role('radio').count() == 4
    assert page.locator('.trip-time>output').all_text_contents() == ['—']*2
    assert page.locator('.trip-time .metric-label').all_text_contents() == ['Time car 1','Time car 2']
    assert page.locator('.metric>output').all_text_contents() == ['—']*4
    assert page.get_by_role('button',name='Simulate',exact=True).is_disabled()
    assert page.locator('.simulation-panel,.results,.brand,.map-header').count() == 0
    assert page.get_by_role('slider').get_attribute('aria-label') != 'How much over speed limit should Car 2 drive'
    assert page.locator('.slider-heading label').inner_text() == 'Car 2 target cruising speed above the limit (%)'
    assert page.locator('.metric-1 .metric-label').inner_text() == 'Car 2 actual average moving-speed increase (%)'
    assert page.locator('.address-box input').evaluate_all("els => els.every(e => e.autocapitalize === 'none')")
    assert page.locator('.metric').evaluate_all("els => els.every(e => e.querySelector('.metric-label').getBoundingClientRect().bottom <= e.querySelector('output').getBoundingClientRect().top)")
    assert page.locator('.slider-heading').evaluate("e => e.querySelector('label').getBoundingClientRect().bottom <= e.querySelector('output').getBoundingClientRect().top")
    page.screenshot(path=str(OUT/'minimal-desktop.png'), full_page=True)
    checks.append({'test':'empty placeholders, 20% default, four icon times and four empty cards; old panels removed','pass':True})

    for label, query in [('Starting point','1 Dr Carlton B Goodlett'),('Destination','100 Van Ness')]:
        field = page.get_by_role('combobox',name=label)
        field.fill(query)
        assert field.input_value() == query
        page.locator('.search-results [role=option]').first.wait_for(timeout=15000)
        assert page.locator('.search-results [role=option] strong').first.inner_text() != page.locator('.search-results [role=option] strong').first.inner_text().upper()
        field.press('ArrowDown')
        field.press('Enter')
    page.get_by_role('radio',name='Midday · 12 PM').check()
    page.get_by_role('radio',name='Midday · 12 PM').focus()
    page.keyboard.press('ArrowRight')
    assert page.get_by_role('radio',name='Evening · 5 PM').is_checked()
    page.get_by_role('radio',name='Morning · 8 AM').check()
    page.get_by_role('button',name='Simulate',exact=True).click()
    page.get_by_role('button',name='Pause simulation').wait_for(timeout=45000)
    page.locator('.car-marker').first.wait_for(state='visible',timeout=30000)
    page.wait_for_timeout(700)
    early = page.locator('.metric>output').all_text_contents()
    assert not any('—' in s for s in early)
    page.get_by_role('button',name='Pause simulation').click()
    paused = page.locator('.metric>output').all_text_contents()
    paused_times = page.locator('.trip-time>output').all_text_contents()
    assert all(t.endswith('min') and t.removesuffix('min').isdigit() for t in paused_times), paused_times
    page.wait_for_timeout(250)
    assert paused == page.locator('.metric>output').all_text_contents()
    assert paused_times == page.locator('.trip-time>output').all_text_contents()
    page.mouse.move(1400,30)
    page.screenshot(path=str(OUT/'minimal-running.png'), full_page=True)
    page.get_by_role('button',name='Resume simulation').click()
    page.wait_for_function("document.querySelector('.metrics').dataset.state === 'finished'", timeout=45000)
    final = page.locator('.metric>output').all_text_contents()
    final_times = page.locator('.trip-time>output').all_text_contents()
    assert final_times != paused_times, (paused_times,final_times)
    car1,car2=(int(t.removesuffix('min')) for t in final_times)
    assert car1>=car2>0,final_times
    page.wait_for_timeout(200)
    assert final_times == page.locator('.trip-time>output').all_text_contents()
    assert final != early, (early,final)
    assert all('Arrived' in title for title in page.locator('.car-marker').evaluate_all('(els)=>els.map(e=>e.title)'))
    page.mouse.move(1400,30)
    page.screenshot(path=str(OUT/'minimal-finished.png'), full_page=True)
    checks.append({'test':'address routing, keyboard time toggle, live values, pause/resume and both arrivals','early':early,'final':final})
    checks.append({'test':'elapsed car times show whole minutes, advance, pause and finalize','paused':paused_times,'final':final_times})

    page.locator('.metric-3').focus()
    assert page.locator('.metric-3 [role=tooltip]').is_visible()
    assert 'Not a measured' in page.locator('.metric-3 [role=tooltip]').inner_text()
    page.get_by_role('slider').fill('0')
    assert page.locator('.trip-time>output').all_text_contents() == ['—']*2
    assert page.locator('.metric>output').all_text_contents() == ['—']*4
    page.get_by_role('button',name='Simulate',exact=True).click()
    page.wait_for_function("document.querySelector('.metrics').dataset.state === 'finished'",timeout=45000)
    assert page.locator('.metric>output').all_text_contents() == ['0.0%']*4
    zero_times=page.locator('.trip-time>output').all_text_contents()
    assert zero_times[0] == zero_times[1] and zero_times[0].endswith('min')
    checks.append({'test':'model detail on focus, changing settings clears results, 0% yields equal cars','pass':True})

    page.get_by_role('button',name='Drop destination pin').click()
    assert page.get_by_role('button',name='Drop destination pin').get_attribute('aria-pressed') == 'true'
    assert page.locator('.maplibregl-canvas').evaluate('(e)=>getComputedStyle(e).cursor') == 'crosshair'
    page.locator('.map-canvas').click(position={'x':1050,'y':350})
    assert ',' in page.get_by_role('combobox',name='Destination').input_value()
    checks.append({'test':'pin placement kept without extra map instructions','pass':True})
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT/'minimal-mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.locator('.trip-time').evaluate_all("els => els.every(e => e.querySelector('.metric-label').getBoundingClientRect().bottom <= e.querySelector('output').getBoundingClientRect().top)")
    assert page.locator('.metric').evaluate_all("els => els.every(e => e.querySelector('.metric-label').getBoundingClientRect().bottom <= e.querySelector('output').getBoundingClientRect().top)")
    checks.append({'test':'responsive layout without horizontal overflow','pass':True})
    browser.close()
report={'checks':checks,'errors':errors}
(OUT/'minimal-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
assert not errors, errors
