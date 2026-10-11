import asyncio,json,re
from pathlib import Path
from urllib.parse import quote_plus
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'metadata'/'web';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
('bing_timing','https://www.bing.com/search?q='+quote_plus('San Francisco signal timing Synchro appendix pdf')),
('bing_cards','https://www.bing.com/search?q='+quote_plus('San Francisco "signal timing" "download"')),
('sfcta_cmp','https://www.sfcta.org/reports/congestion-management-program-2025'),
('sfcta_dta','https://www.sfcta.org/tools-data/dynamic-traffic-assignment'),
('sfmta_counts','https://www.sfmta.com/TrafficCounts'),
('planning_library','https://sfplanning.org/environmental-review-documents'),
('arcgis_traffic','https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer'),
('arcgis_datasf','https://services.sfmta.com/arcgis/rest/services/DataSF/master/FeatureServer'),
]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context()
  for key,url in SOURCES:
   if (OUT/(key+'.json')).exists():continue
   page=await c.new_page()
   try:
    response=await page.goto(url,wait_until='domcontentloaded',timeout=60000)
    await page.wait_for_timeout(1500)
    body=await page.locator('body').inner_text()
    links=await page.locator('a[href]').evaluate_all('(els)=>els.map(e=>({text:e.innerText,url:e.href}))')
    obj={'url':url,'final_url':page.url,'status':response.status,'text':body,'links':links}
    (OUT/(key+'.json')).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    relevant=[l for l in links if re.search(r'pdf|\.csv|\.zip|\.xlsx|synchro|timing|traffic|speed|appendi|transportation|download|signal|greenwave',l['text']+' '+l['url'],re.I)]
    print(key,'STATUS',response.status,'TEXT',body[:180].replace('\n',' '),'LINKS',len(links),flush=True)
    for l in relevant[:70]:print(json.dumps(l,ensure_ascii=True),flush=True)
   except Exception as e:print('ERROR',key,str(e),flush=True)
   await page.close()
  await b.close()
if __name__=='__main__':asyncio.run(main())
