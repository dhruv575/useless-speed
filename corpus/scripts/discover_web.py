import asyncio,json,re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
QUERIES=[
 'San Francisco signal timing cards download data',
 'site.sfplanning.org "Cycle Length" "Offset"',
 'site.sfcta.org "signal timing" download',
 'San Francisco Synchro traffic signal timing appendix pdf',
 'site.sfmta.com "timing cards"',
]
async def main():
    out=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        for q in QUERIES:
            await page.goto('https://www.google.com/search?q='+quote(q),wait_until='domcontentloaded')
            text=await page.locator('body').inner_text()
            links=await page.locator('a').evaluate_all('(aa)=>aa.map(a=>({text:a.innerText,url:a.href})).filter(a=>a.text && a.url.startsWith("http"))')
            out.append({'query':q,'page_url':page.url,'text':text,'links':links})
            print(q,text[:400],flush=True)
            if 'unusual traffic' in text.lower() or 'not a robot' in text.lower(): break
        (ROOT/'metadata'/'web_search.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
        await browser.close()
asyncio.run(main())
