"""Check what powerLevel values Firestone actually returns."""
from playwright.sync_api import sync_playwright
import json, gzip as gz

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    captured = {}
    def on_resp(resp):
        url = resp.url
        if "bgs-comps-strategies" in url:
            try:
                body = resp.body()
                try: body = gz.decompress(body)
                except: pass
                captured['data'] = json.loads(body.decode('utf-8', 'ignore'))
            except: pass
    page.on("response", on_resp)
    try:
        page.goto("https://www.firestoneapp.com/battlegrounds/comps",
                  wait_until="networkidle", timeout=40000)
    except: pass
    browser.close()

if 'data' not in captured:
    print("No data captured!")
else:
    for cd in captured['data']:
        cid = cd.get('compId', '?')
        pl = cd.get('powerLevel', 'MISSING')
        diff = cd.get('difficulty', '?')
        name = cd.get('name', '?')
        print(f"  {cid:30s} powerLevel={pl!r:15s} diff={diff!r:10s} name={name}")
