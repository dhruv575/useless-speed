"""Generate an offline browser catalog and human-readable collection notes."""
import json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DER=ROOT/'derived'
def read(name):return json.loads((DER/name).read_text(encoding='utf-8'))
def main():
 stats=read('statistics.json');docs=read('catalog.json');pages=read('timing_pages.json');cards=read('verified_timing_cards.json')
 datasets=[r for r in docs if not r['duplicate_of'] and r['category'] in ['observed_speeds','road_geometry','traffic_counts','gis_context']]
 payload={'stats':stats,'documents':[r for r in docs if not r['duplicate_of']],'pages':pages,'cards':cards}
 template=r'''<!doctype html><html lang="en" autocapitalize="none"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Useless Speed | Research corpus</title>
<style>
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#1a2b3b;background:#f5f7fa;font-size:15px}*{box-sizing:border-box}body{margin:0}main{max-width:1240px;margin:auto;padding:46px 28px}header{max-width:920px}.eyebrow{font-size:12px;letter-spacing:.16em;font-weight:700;color:#487285;text-transform:none}h1{font-size:36px;line-height:1.12;letter-spacing:-.035em;margin:14px 0}h2{font-size:18px}p{line-height:1.6}.intro{color:#526578;max-width:830px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}.stat{background:#fff;border:1px solid #dfe5ea;border-radius:12px;padding:18px}.stat b{display:block;font-size:27px;letter-spacing:-.03em}.stat span{color:#526578;font-size:13px}.note{border-left:3px solid #b88b45;background:#fff9ee;padding:12px 17px;line-height:1.55;border-radius:0 8px 8px 0;font-size:14px}a{color:#176778;text-underline-offset:3px}nav{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 32px}.controls{display:flex;gap:12px;margin:24px 0 12px;flex-wrap:wrap}input,select,button{font:inherit;border:1px solid #bac8d2;border-radius:8px;background:white;padding:12px;color:inherit}input{flex:1;min-width:240px}input:focus,select:focus{outline:2px solid #3090a1;outline-offset:2px}#count{font-size:13px;color:#596e7e;margin:14px 0}.item{background:#fff;border:1px solid #dfe5ea;border-radius:10px;padding:19px 21px;margin:10px 0}.item h3{font-size:16px;margin:7px 0 9px;line-height:1.4}.meta{font-size:12px;text-transform:none;letter-spacing:.05em;color:#5c7383}.snippet{font-size:13px;color:#3f5565;white-space:pre-wrap;line-height:1.6}.links{display:flex;gap:18px;font-size:13px;margin-top:13px}.tag{display:inline-block;border:1px solid #c9dfdb;border-radius:5px;color:#225d53;background:#f2faf8;padding:4px 7px;font-size:12px;margin:0 6px 5px 0}details{background:#fff;border:1px solid #dfe5ea;border-radius:10px;padding:16px 20px;margin-top:24px}summary{cursor:pointer;font-weight:650}code{font-family:Consolas,monospace;font-size:13px;background:#eef2f5;padding:2px 5px}footer{color:#667887;margin-top:34px;font-size:13px}#more{display:block;margin:20px auto}.empty{padding:40px;text-align:center}@media(max-width:650px){main{padding:26px 16px}h1{font-size:30px}.stats{grid-template-columns:repeat(2,1fr)}.controls>*{width:100%}}
</style><main><header><div class="eyebrow">Research collection · collected October 10, 2026</div><h1>San Francisco<br>signal & traffic corpus</h1><p class="intro">Published signal timing cards, engineering plans, transportation models, and observed traffic data. Search the source collection and jump directly to promising pages.</p></header><div id="stats" class="stats"></div>
<div class="note"><strong>Read the evidence in context.</strong> Timing cards are dated records; transportation studies include existing and proposed scenarios. Modeled cycles, actuation, and priority settings are not live red-light observations. This is a research corpus, not a verified current citywide timing database.</div>
<nav><a href="README.md">Collection notes</a><a href="derived/catalog.csv">File catalog CSV</a><a href="derived/timing_pages.csv">Timing pages CSV</a><a href="derived/verified_timing_plans.csv">Checked card subset</a><a href="derived/corpus.sqlite">Full-text SQLite index</a><a href="metadata/failures.json">Unavailable files</a></nav>
<details><summary>Three intersections with checked agency timing-card details</summary><div id="cards"></div></details>
<div class="controls"><input id="search" type="search" aria-label="Search titles, streets and timing excerpts" placeholder="Search titles, streets, or timing excerpts…"><select id="view" aria-label="Collection view"><option value="timing">Labeled timing pages</option><option value="pages">All timing mentions</option><option value="sources">All unique source files</option><option value="data">Speed, count & GIS datasets</option></select></div><div id="count" aria-live="polite"></div><div id="results"></div><button id="more">Show 50 more</button>
<details><summary>Search every extracted page</summary><p>The search box covers document titles and timing excerpts. For complete extracted text, use the local SQLite FTS index:</p><p><code>python corpus/scripts/query.py 'Synchro AND Existing'</code></p><p><code>python corpus/scripts/query.py '"Ocean Avenue"' --limit 20</code></p><p>PDF page numbers are one-based. Workbook results use sheet sequence numbers. OCR is marked and should be checked against the original scan.</p></details><footer>All files remain local. No account, tracking, or network connection is required to search this catalog. Original-source links require internet access.</footer></main>
<script id="data" type="application/json">__DATA__</script><script>
const D=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id),fmt=n=>n.toLocaleString(),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),href=p=>p.split('/').map(encodeURIComponent).join('/');
$('stats').innerHTML=[[D.stats.unique_files,'unique source files'],[D.stats.unique_pdf_pages,'PDF pages'],[D.stats.labeled_timing_pages,'pages with labeled timing'],[1571371,'hourly speed records']].map(([n,t])=>`<div class="stat"><b>${fmt(n)}</b><span>${t}</span></div>`).join('');
$('cards').innerHTML=D.cards.filter(c=>c.document_id!=='16282597').map(c=>`<p><strong>${esc(c.intersection)}</strong> · revision ${esc(c.revision_date)}<br>${esc(c.plans.filter(p=>p.cycle_seconds).map(p=>p.cycle_seconds+'s / '+p.offset_seconds+'s offset').filter((v,i,a)=>a.indexOf(v)===i).join('; ')||'FREE operation; nightly FLASH')}<br><a href="${href(c.local_path)}#page=1" target="_blank" rel="noreferrer">Open original card</a> · <a href="${esc(c.source_url)}" target="_blank" rel="noreferrer">Public source</a></p>`).join('');
let limit=50;const categories=new Set(['observed_speeds','road_geometry','traffic_counts','gis_context']);
function render(){const mode=$('view').value,q=$('search').value.toLowerCase().trim(),isPage=['timing','pages'].includes(mode);let rows=isPage?D.pages.filter(r=>mode==='pages'||r.strength==='labeled_timing'):D.documents.filter(r=>mode!=='data'||categories.has(r.category));if(q)rows=rows.filter(r=>JSON.stringify([r.title,r.category,r.heading_candidates,r.scenario_context,r.verbatim_timing_lines,r.snippets,r.cycle_length_seconds_candidates,r.actuated_cycle_seconds_candidates]).toLowerCase().includes(q));$('count').textContent=fmt(rows.length)+' results · showing '+Math.min(rows.length,limit)+(isPage?' · modeled scenarios and repeats are separate pages':' · byte-identical duplicates collapsed');$('results').innerHTML=rows.slice(0,limit).map(r=>{const cycle=[...(r.cycle_length_seconds_candidates||[]),...(r.actuated_cycle_seconds_candidates||[])];const tags=(cycle.length?`<span class="tag">Cycle candidate: ${esc(cycle.join(', '))} s</span>`:'')+(r.machine_ocr?'<span class="tag">Machine OCR</span>':'');let desc=isPage?(r.verbatim_timing_lines?.join('\n')||r.snippets?.slice(0,2).join('\n')||'Timing-card page. Open the original to inspect its table.'):((r.extraction?.page_count?fmt(r.extraction.page_count)+' PDF pages · ':'')+(r.row_count||r.feature_count||r.extraction?.row_count?fmt(r.row_count||r.feature_count||r.extraction.row_count)+' records · ':'')+(r.bytes/1048576).toFixed(2)+' MB');return `<article class="item"><div class="meta">${esc(r.category.replaceAll('_',' '))}${isPage?' · page '+r.pdf_page:''}</div><h3>${esc(r.title)}</h3>${tags}<div class="snippet">${esc(desc)}</div>${r.scenario_context?.length?`<p class="snippet">Scenario cues: ${esc(r.scenario_context.slice(0,2).join(' · '))}</p>`:''}<div class="links"><a href="${href(r.local_path)}${isPage?'#page='+r.pdf_page:''}" target="_blank" rel="noreferrer">Open local file${isPage?' at page '+r.pdf_page:''}</a><a href="${esc(r.source_url)}" target="_blank" rel="noreferrer">Public source</a>${r.text_path?`<a href="${href(r.text_path)}" target="_blank">Extracted text</a>`:''}</div></article>`}).join('')||'<div class="empty">No matches. Try a street name, Synchro, or another view.</div>';$('more').hidden=rows.length<=limit;}
$('search').addEventListener('input',()=>{limit=50;render()});$('view').addEventListener('change',()=>{limit=50;render()});$('more').addEventListener('click',()=>{limit+=50;render()});render();
</script></html>'''
 (ROOT/'index.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8')
 table='\n'.join(f'| [{r["title"]}]({r["local_path"]}) | {r.get("row_count",r.get("feature_count",r.get("extraction",{}).get("row_count",0))):,} | {r.get("date_min",r.get("year_min",""))}–{r.get("date_max",r.get("year_max",""))} |' for r in datasets)
 notes=f'''# San Francisco signal and traffic research corpus

Part of [Useless Speed](../README.md). For installation and current reproduction commands, see [the reproduction guide](../docs/reproducing.md).

Collected with isolated, headless Chrome on October 10, 2026 (Pacific time). No new public-records requests were submitted. Start with [the offline searchable catalog](index.html).

## What is here

- **{stats['unique_files']:,} unique source files** across {stats['source_files']:,} successful source records; {stats['duplicates']:,} byte-identical duplicates are marked, not counted twice in search.
- **{stats['unique_pdf_pages']:,} PDF pages**, with **{stats['labeled_timing_pages']:,} candidate pages containing labeled timing** and {stats['timing_candidate_pages']:,} pages with timing/model mentions. These are pages, not distinct intersections or verified operating plans.
- Original PDF timing cards, three timing-workbook variants, Synchro 12 and SimTraffic files, signal drawings/CAD, and transportation-study appendices.
- SFCTA speed observations: **1,571,371 hourly segment records**, **132,940 peak-period segment records**, and historical corridor observations from **1991–2025**. Monthly data spans **January 2019–September 2026**; availability differs by segment and month.
- Citywide signal inventory, speed-limit segments, lane and one-way geometry, green-wave locations, and SFMTA traffic counts.
- Original-source URLs, SHA-256 hashes, byte sizes, retrieval timestamps, download failures, machine-readable page candidates, and a full-text SQLite index.

The retained selected originals occupy {stats['total_bytes']/1e9:.2f} GB ({stats['unique_bytes']/1e9:.2f} GB unique content). This public bundle includes selected cataloged originals; exploratory downloads are not included. Use the catalog rather than raw file counts for coverage.

## Best starting points

| Evidence | What it establishes |
|---|---|
| [Checked timing-card subset](derived/verified_timing_cards.json) | Dated settings for 19th/Sloat (2015 existing plus a separate 2014 draft), 3rd/25th (2024), and 41st/Chain of Lakes/Lincoln (2025). Four source documents, three intersections. |
| [Checked plan rows](derived/verified_timing_plans.csv) | Small manual subset of cycles, offsets, schedule/mode, revision date, source page, and caveats. |
| [All timing candidate pages](derived/timing_pages.csv) | Jump to labeled values and Synchro pages. Includes modeled existing, future, and project scenarios. |
| [Full file catalog](derived/catalog.csv) | Source URL, file path, hash, category, duplicate relationship. |
| [Structured catalog](derived/catalog.json) | Adds extraction method, PDF/sheet counts, schema and record counts. |
| [SQLite full-text database](derived/corpus.sqlite) | Search extracted PDF pages, workbook sheets and relevant correspondence. |

For example, the 2015 19th/Sloat card contains 100- and 120-second schedules with offsets. The 2024 3rd/25th card contains 120-second coordinated plans, FREE periods, transit priority, and preemption. The 2025 41st/Lincoln card specifies isolated FREE operation and nightly FLASH. These examples already show why a universal fixed-red-light model would be inadequate.

## Data snapshots

| Dataset | Records/features | Source period, when provided |
|---|---:|---|
{table}

Raw JSON/GeoJSON is retained. Tabular UTF-8 exports are in [derived/tables](derived/tables). GIS schemas and coded-value domains are archived alongside the original data. Geometry remains available in GeoJSON; a CSV geometry column is serialized JSON.

## Coverage and interpretation

This is **not a verified current citywide cycle/offset database**. Timing cards are dated agency records. Engineering designs can be drafts. Transportation reports contain scenario assumptions, and repeated intersections across AM/PM, future years, and alternatives. A reference to a timing card is not itself the card.

Automatically extracted cycle and offset values are **candidates**. Each retains its verbatim line and PDF page. No automatic join asserts that an extracted number belongs to a particular current controller. Actuated cycle length in a model is distinguished from nominal cycle length. Blank offsets and FREE are not converted to zero. Only the small checked subset has been manually reviewed.

{stats.get('ocr_pages',0)} primary-card pages have local OCR, with bounding boxes and confidence scores in [derived/ocr](derived/ocr). {stats['sparse_pdf_pages_without_ocr']:,} other PDF pages have sparse text and no OCR; many are maps, images, or scans. Native CAD, Synchro/SimTraffic, and archive files are preserved but have not been simulated or decoded into controller settings. ZIPs are inventoried without expansion. Workbook extraction retains formulas and cached values without recalculating them.

The SFCTA `inrix_rt_weekly_exp` endpoint is the **monthly dashboard's** underlying table despite its name. Its `year` field is 2020 throughout this snapshot while `date` spans 2019–2026; use `date` and preserve that source anomaly. The hourly table has month/date, hour period, segment ID, and mean speed—not vehicle trajectories or second-by-second light states. Dashboard labels give speeds in mph. Aggregates overlap their underlying observations and should not be added as independent measurements.

Testing the original speeding/red-light hypothesis would still require a route model: signal sequence, offsets/reference phases, time-of-day plans, actuation/priority behavior, queues, acceleration, and matched departure times. This corpus supplies useful inputs and observed-speed context, but does not itself measure a causal travel-time benefit from speeding.

## Collection method and limits

1. Searched public NextRequest document titles using ten timing/model/traffic terms and searched request descriptions. Expanded narrowly relevant requests and downloaded technical attachments. Search-result and request metadata are retained under `metadata/`; those discovery records are not all relevant corpus files.
2. Scanned all **50 pages / 492 entries** of the SF Planning environmental-review library. Downloaded transportation attachments and selected bundled appendices. For retired `sfmea`, `archives`, and `default` hosts, resolved public files in SF Planning's S3 archive and recorded the successful URL.
3. Read public ArcGIS layer directories and downloaded every feature, verifying returned feature counts against the layer count endpoint.
4. Captured SFCTA dashboard network requests and downloaded the exposed data. Returned row counts were checked against HTTP Content-Range totals.
5. Preserved originals, checked file signatures, hashed files, extracted text/cells, identified duplicates, indexed pages, and visually inspected representative primary timing cards.

The corpus includes selected historical plans for 19th Avenue, 41st/Lincoln, 3rd/25th, and other intersections; reports cover Better Market Street, Stonestown, Balboa Reservoir, the Hub, India Basin, Potrero Power Station, Central SoMa and additional areas. Spatial coverage is uneven.

See [failed downloads](metadata/failures.json). Six Planning shared links reported an expired or invalid link; an older duplicate SFMTA count link returned 404 while its current replacement downloaded successfully. Some SFCTA main-site pages required browser security verification, but the public dashboards and their data endpoints worked. NextRequest request `26-9464` attachment pagination stopped after 100 metadata records with server errors; `25-131` also returned an attachment-list server error. These are recorded gaps, not evidence that records do not exist. No comprehensive citywide operational SPaT feed was established by this collection.

## Use and reproduce

Open `index.html` directly; it embeds the catalog and works offline. The browser search covers titles, scenario cues, and timing excerpts. For complete extracted text, run:

```powershell
python corpus/scripts/query.py 'Synchro AND Existing'
python corpus/scripts/query.py '"Ocean Avenue"' --limit 20
python corpus/scripts/query.py '"signal timing"' --json
```

The database has `documents` and FTS5 `pages` tables. Page numbers are one-based PDF pages; workbook results use sheet sequence numbers. Document hashes join the text, page, workbook and OCR artifacts.

Collection scripts use public requests inside an isolated Playwright Chromium context with `headless=True`. They do not use your Chrome profile. Key scripts:

```powershell
python -m venv .venv
# Activate it, then install corpus/requirements.txt and Playwright Chromium.
python corpus/scripts/collect_curated.py
python corpus/scripts/collect_planning.py
python corpus/scripts/download_planning.py
python corpus/scripts/collect_supporting.py
python corpus/scripts/probe_dashboards.py
python corpus/scripts/collect_speeds.py
python corpus/scripts/ocr_cards.py
python corpus/scripts/build_index.py
python corpus/scripts/verified_cards.py
python corpus/scripts/publish_catalog.py
```

Existing metadata/downloads are reused. To update discovery rather than reproduce this snapshot, review the saved search/query lists and website pagination; future endpoints and document links can change. `collect_curated.py` uses the archived global searches as its starting catalog. Download manifests and relevant public discovery metadata are retained for provenance; transient logs and website response bodies are omitted.

## Primary portals

- [San Francisco public records archive](https://sanfrancisco.nextrequest.com/documents)
- [41st/Lincoln public request 25-2143](https://sanfrancisco.nextrequest.com/requests/25-2143)
- [19th Avenue public request 22-3290](https://sanfrancisco.nextrequest.com/requests/22-3290)
- [3rd/25th public request 25-1486](https://sanfrancisco.nextrequest.com/requests/25-1486)
- [SF Planning environmental review library](https://sfplanning.org/environmental-review-documents)
- [SFMTA traffic counts](https://www.sfmta.com/TrafficCounts)
- [SFMTA traffic GIS layers](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer)
- [SFCTA congestion dashboard](https://congestion.sfcta.org/)
- [SFCTA Congestion Management Program dashboard](https://cmp.sfcta.org/)
'''
 (ROOT/'README.md').write_text(notes,encoding='utf-8')
 print('Published index.html and README.md')
if __name__=='__main__':main()
