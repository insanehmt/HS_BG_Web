"""Fetch Firestone comps data via Playwright and print structure."""
from playwright.sync_api import sync_playwright
import gzip, json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    data = {}
    def on_response(resp):
        url = resp.url
        if 'bgs-comps-strategies' in url or 'comp-stats' in url:
            try:
                body = resp.body()
                try:
                    body = gzip.decompress(body)
                except Exception:
                    pass
                data[url] = json.loads(body.decode('utf-8', 'ignore'))
            except Exception:
                pass

    page.on('response', on_response)
    page.goto('https://www.firestoneapp.com/battlegrounds/comps', wait_until='networkidle', timeout=30000)

    for url, d in data.items():
        if 'strategies' in url:
            comps = [c for c in d if c.get('compId') and c.get('cards')]
            print('Total comps with cards:', len(comps))
            print()
            print('Sample comp:')
            print(json.dumps(comps[0], indent=2, ensure_ascii=False))
            print()
            print('All compIds:')
            for c in comps:
                cid = c['compId']
                power = c.get('powerLevel', '-')
                diff = c.get('difficulty', '-')
                ncards = len(c['cards'])
                tribes = c.get('forcedTribes', [])
                print(f'  {cid:35s} power={power} diff={diff} cards={ncards} tribes={tribes}')

        if 'comp-stats' in url:
            stats = d.get('compStats', [])
            print()
            print('Comp stats count:', len(stats))
            for s in stats[:5]:
                arch = s['archetype']
                avg = round(s['averagePlacement'], 2)
                dp = s['dataPoints']
                print(f'  archetype={arch:35s} avg={avg} dataPoints={dp}')

    browser.close()
