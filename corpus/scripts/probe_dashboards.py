import asyncio,json,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'metadata'/'dashboard_network';OUT.mkdir(parents=True,exist_ok=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context()
  for name,url in [('cmp','https://cmp.sfcta.org'),('congestion','https://congestion.sfcta.org'),('dta_archive','http://code.google.com/p/dta/downloads/detail?name=SFDTAFinalMethodologyReport_113012.pdf')]:
   page=await c.new_page();events=[];tasks=[]
   async def capture(r):
    if any(x in r.url for x in ['mapbox','google-analytics','analytics.google','tile.openstreetmap','gstatic','googletagmanager']):return
    row={'url':r.url,'status':r.status,'content_type':r.headers.get('content-type','')};events.append(row)
    if re.search(r'json|javascript',row['content_type']) and r.status==200:
     try:
      body=await r.text();file=f'{name}_{len(events):03}.txt';(OUT/file).write_text(body,encoding='utf-8');row['body_file']=file
     except:pass
   page.on('response',lambda r:tasks.append(asyncio.create_task(capture(r))))
   try:
    await page.goto(url,wait_until='domcontentloaded',timeout=60000);await page.wait_for_timeout(5000)
    text=await page.locator('body').inner_text();links=await page.locator('a[href]').evaluate_all('es=>es.map(e=>({title:e.innerText,url:e.href}))')
    (OUT/(name+'_page.json')).write_text(json.dumps({'url':page.url,'text':text,'links':links},ensure_ascii=False,indent=2),encoding='utf-8')
   except Exception as e:print('ERROR',name,str(e),flush=True)
   await asyncio.gather(*tasks,return_exceptions=True)
   (OUT/(name+'_network.json')).write_text(json.dumps(events,indent=2),encoding='utf-8');await page.close()
   print(name,[(e['status'],e['url']) for e in events if not re.search(r'\.js|\.css|\.png|woff|bootstrap',e['url'])],flush=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
