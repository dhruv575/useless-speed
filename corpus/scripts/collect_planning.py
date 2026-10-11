"""Discover transportation attachments across the public environmental library."""
import asyncio,json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]; META=ROOT/'metadata'/'planning';META.mkdir(parents=True,exist_ok=True)
BASE='https://sfplanning.org/environmental-review-documents'
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context()
  page=await c.new_page();await page.goto(BASE,wait_until='domcontentloaded')
  forms=await page.locator('select').evaluate_all('(es)=>es.map(e=>({name:e.name,options:Array.from(e.options).map(o=>({value:o.value,text:o.text}))}))')
  save(META/'form_options.json',forms)
  print('FORM',json.dumps(forms,ensure_ascii=True),flush=True)
  links=[]; projects=[]
  # The library exposes 50 pages in its public pager. Retain row context so
  # identically titled appendices remain associated with the correct project.
  for pn in range(50):
   cache=META/f'page_{pn:02}.json'
   if cache.exists():obj=json.loads(cache.read_text(encoding='utf-8'))
   else:
    try:
     await page.goto(BASE+f'?page={pn}',wait_until='domcontentloaded',timeout=60000)
     rows=await page.locator('table tbody tr').evaluate_all('es=>es.map(e=>({text:e.innerText,links:Array.from(e.querySelectorAll("a[href]")).map(a=>({title:a.innerText,url:a.href}))}))')
     obj={'url':page.url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'rows':rows}
     save(cache,obj)
    except Exception as e:print('PAGE ERROR',pn,str(e),flush=True);continue
   projects.extend(obj['rows'])
   for row in obj['rows']:
    project=row['text'].split('\n')[0].strip()
    for l in row['links']:
     if re.search(r'transport|traffic|synchro|intersection|level.of.service',l['title'],re.I):
      links.append({**l,'project':project,'discovery_url':obj['url']})
   print('PAGE',pn,'PROJECTS',len(projects),'TRANSPORT LINKS',len(links),flush=True)
   await asyncio.sleep(.25)
  uniq={l['url']:l for l in links};save(META/'transportation_links.json',list(uniq.values()));save(META/'projects.json',projects)
  print('DISCOVERY COMPLETE',len(projects),len(uniq),flush=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
