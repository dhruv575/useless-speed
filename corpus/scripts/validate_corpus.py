import asyncio,hashlib,json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1];DER=ROOT/'derived'
async def main():
 docs=json.loads((DER/'catalog.json').read_text(encoding='utf-8'));problems=[]
 for d in docs:
  p=ROOT/d['local_path']
  if not p.exists():problems.append([d['id'],'missing file']);continue
  h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
  if h!=d['sha256']:problems.append([d['id'],'hash mismatch'])
  if p.stat().st_size!=d['bytes']:problems.append([d['id'],'size mismatch'])
  if d.get('feature_count') is not None and d['feature_count']!=d['expected_count']:problems.append([d['id'],'GIS count mismatch'])
  if d.get('content_range') and int(d['content_range'].split('/')[-1])!=d['row_count']:problems.append([d['id'],'API count mismatch'])
 pages=json.loads((DER/'timing_pages.json').read_text(encoding='utf-8'));ids={d['id']:d for d in docs}
 for p in pages:
  d=ids[p['document_id']];maxpage=d['extraction'].get('page_count',d['extraction'].get('sheets',0))
  if not 1<=p['pdf_page']<=maxpage:problems.append([d['id'],'invalid page pointer',p['pdf_page']])
 con=sqlite3.connect(DER/'corpus.sqlite');integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
 query_count=con.execute("SELECT count(*) FROM pages WHERE pages MATCH '\"Ocean Avenue\"'").fetchone()[0];con.close()
 if integrity!='ok' or query_count==0:problems.append(['sqlite',integrity,query_count])
 ui={};errors=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True);page=await browser.new_page(viewport={'width':1440,'height':1080})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto((ROOT/'index.html').as_uri());await page.locator('article').first.wait_for()
  ui['initial_count']=await page.locator('#count').inner_text()
  await page.get_by_role('searchbox').fill('Ocean')
  ui['ocean_search']=await page.locator('#count').inner_text();ui['ocean_articles']=await page.locator('article').count()
  await page.get_by_role('searchbox').fill('');await page.locator('#view').select_option('data')
  ui['data_count']=await page.locator('#count').inner_text();ui['data_articles']=await page.locator('article').count()
  await page.locator('#view').select_option('timing')
  await page.screenshot(path=str(DER/'catalog-preview.png'),full_page=False)
  ui['browser_errors']=errors;await browser.close()
 if errors or ui['ocean_articles']==0 or ui['data_articles']==0:problems.append(['browser',ui])
 report={'checked_at':datetime.now(timezone.utc).isoformat(),'hashes_checked':len(docs),'page_pointers_checked':len(pages),'sqlite_integrity':integrity,'ocean_avenue_fts_matches':query_count,'headless_browser':ui,'problems':problems}
 (DER/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
 if problems:raise SystemExit(1)
if __name__=='__main__':asyncio.run(main())
