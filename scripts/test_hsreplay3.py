"""Parse HSReplay JS bundle for comp data."""
from playwright.sync_api import sync_playwright
import json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    )
    page = ctx.new_page()

    js_store = {}
    def on_resp(resp):
        url = resp.url
        if 'battlegrounds_comps' in url and '.js' in url:
            try:
                js_store['js'] = resp.body().decode('utf-8', 'ignore')
                js_store['url'] = url
            except Exception:
                pass

    page.on('response', on_resp)
    try:
        page.goto('https://hsreplay.net/battlegrounds/comps/', wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    time.sleep(8)

    js = js_store.get('js', '')
    print('JS bundle size:', len(js))

    # Find BG card IDs in JS bundle
    all_ids = re.findall(r'\b(BG[A-Z0-9_]{3,}|BGS_\d+)\b', js)
    unique = list(dict.fromkeys(all_ids))
    print('Card IDs in JS:', len(unique))
    print(unique[:30])

    # Look for comp name patterns
    comp_names = re.findall(r'"([A-Za-z\s\-]+(?:Demons?|Undead|Murloc|Beast|Dragon|Mech|Pirate|Naga|Quilboar|Elemental)[^"]{0,40})"', js)
    print()
    print('Comp names in JS:', len(comp_names))
    for n in comp_names[:20]:
        print(' ', n)

    # Look for archetype data
    idx = js.find('archetype')
    if idx >= 0:
        print()
        print('archetype context:')
        print(js[idx-50:idx+300])

    # Look for tier data
    for kw in ['"tier"', 'comps:', 'compositions:']:
        idx = js.find(kw)
        if idx >= 0:
            print(f'\n{kw!r} context:')
            print(js[idx:idx+400])

    browser.close()
