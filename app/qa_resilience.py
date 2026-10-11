"""Production assets, endpoint validation, error recovery and map fallback."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

out=Path(__file__).parent/'test-output'
out.mkdir(exist_ok=True)
report=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1440,'height':900})
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:8788/',wait_until='domcontentloaded')
    page.wait_for_function("!document.querySelector('.configuration').disabled")
    for label,query in [('Starting point','1 Dr Carlton B Goodlett'),('Destination','100 Van Ness')]:
        field=page.get_by_role('combobox',name=label)
        field.fill(query)
        page.locator('.search-results [role=option]').first.wait_for(timeout=15000)
        field.press('ArrowDown')
        field.press('Enter')
    page.get_by_role('button',name='Simulate',exact=True).click()
    page.get_by_role('button',name='Pause simulation').wait_for(timeout=45000)
    page.get_by_role('button',name='Pause simulation').click()
    page.locator('.car-marker').first.wait_for(state='visible',timeout=30000)
    assert not errors,errors
    report.append({'test':'production bundle and map worker','pass':True,'errors':list(errors)})
    for query in ['start=0,0&end=-122.4,37.7','start=-122.42,37.77&end=-122.42,37.77','start=NaN,37.7&end=-122.4,37.7']:
        response=context.request.get('http://127.0.0.1:8788/api/route?'+query)
        assert response.status==400
    report.append({'test':'invalid and coincident route coordinates rejected','pass':True})
    page.wait_for_timeout(600)
    box=page.locator('.map-endpoint.end').bounding_box()
    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
    page.mouse.down()
    page.mouse.move(box['x']+box['width']/2+90,box['y']+box['height']/2-100,steps=12)
    page.mouse.up()
    assert ',' in page.get_by_role('combobox',name='Destination').input_value()
    page.route('**/api/route?*',lambda route: route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'Routing is temporarily unavailable.'})))
    page.get_by_role('button',name='Simulate',exact=True).click()
    page.get_by_role('alert').wait_for(timeout=10000)
    assert 'Routing is temporarily unavailable' in page.get_by_role('alert').inner_text()
    page.unroute('**/api/route?*')
    page.get_by_role('button',name='Simulate',exact=True).click()
    page.get_by_role('button',name='Pause simulation').wait_for(timeout=45000)
    page.get_by_role('button',name='Pause simulation').click()
    assert page.get_by_role('alert').count()==0
    report.append({'test':'pin dragging, routing error and retry recovery','pass':True})
    fallback=browser.new_context(viewport={'width':1280,'height':850})
    fallback.route('https://tiles.openfreemap.org/**',lambda route: route.abort())
    offline=fallback.new_page()
    offline.goto('http://127.0.0.1:8788/',wait_until='domcontentloaded')
    offline.wait_for_function("!document.querySelector('.configuration').disabled")
    offline.get_by_text('Map tiles unavailable. Showing the local street network.').wait_for(timeout=30000)
    offline.wait_for_timeout(1200)
    offline.screenshot(path=str(out/'minimal-map-fallback.png'))
    report.append({'test':'blocked tile provider retains local street map','pass':True})
    browser.close()
(out/'resilience-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
