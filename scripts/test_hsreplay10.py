"""Final HSReplay scraper - parse comps with tiers via body text + card IDs."""
from playwright.sync_api import sync_playwright
import json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={'width':1280,'height':900}
    )
    page = ctx.new_page()

    try:
        page.goto('https://hsreplay.net/battlegrounds/comps/', wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    time.sleep(15)

    result = page.evaluate("""() => {
        var minLinks = Array.from(document.querySelectorAll('a[href*="/battlegrounds/minions/"]'));
        var seen = new Set();
        var comps = [];

        for (var link of minLinks) {
            var el = link;
            var compEl = null;
            for (var j = 0; j < 15; j++) {
                el = el.parentElement;
                if (!el) break;
                var cnt = el.querySelectorAll('a[href*="/battlegrounds/minions/"]').length;
                if (cnt >= 4 && cnt <= 16) { compEl = el; break; }
            }
            if (!compEl || seen.has(compEl)) continue;
            seen.add(compEl);

            var cards = Array.from(compEl.querySelectorAll('a[href*="/battlegrounds/minions/"]')).map(function(a) {
                var img = a.querySelector('img');
                var src = img ? img.src : '';
                var m = src.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);
                return m ? m[1] : '';
            }).filter(Boolean);

            // Walk UP to find comp name + tier
            var nameEl = compEl;
            var compName = '', difficulty = '', tier = '';
            for (var k = 0; k < 12; k++) {
                nameEl = nameEl.parentElement;
                if (!nameEl) break;
                var text = nameEl.innerText || '';
                var lines = text.split('\\n').map(function(s){return s.trim();}).filter(Boolean);
                for (var line of lines) {
                    if ((line==='S'||line==='A'||line==='B'||line==='C') && !tier) tier=line;
                    if (/Medium|Easy|Hard/.test(line) && !difficulty) difficulty=line;
                    if (/[A-Za-z]{4,}/.test(line) && !/Medium|Easy|Hard|hearthstone|Comps|Heroes|Guides|Season|Tier7|HSReplay|Social|Download|Copyright|navigation|Battlegrounds|Sign|Match|Last|Powered|JeefHS/.test(line) && !compName && line.length < 60) {
                        compName = line;
                    }
                }
                if (compName && tier) break;
            }
            comps.push({name: compName, tier: tier, difficulty: difficulty, cards: cards});
        }

        // Also get page body text to parse tier order
        var bodyText = document.body.innerText;
        return {comps: comps, bodyText: bodyText.substring(0, 4000)};
    }""")

    comps = result['comps']
    body = result['bodyText']

    # Parse tier order from body text
    tier_order = []
    for line in body.split('\n'):
        l = line.strip()
        if l in ('S', 'A', 'B', 'C'):
            tier_order.append(l)

    print('Tier order from body text:', tier_order)
    print()

    # Match tier to comp (body text order matches DOM order)
    # Find comp names in order from body text
    comp_name_order = []
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        l = lines[i]
        if l in ('S', 'A', 'B', 'C'):
            # Next non-empty line might be comp name
            for j in range(i+1, min(i+5, len(lines))):
                candidate = lines[j].strip()
                if len(candidate) > 5 and re.search(r'[A-Za-z]{4}', candidate) and candidate not in ('S','A','B','C','Medium','Easy','Hard'):
                    comp_name_order.append((l, candidate))
                    i = j
                    break
        i += 1

    print('Comp names from body text:')
    for tier, name in comp_name_order:
        print(f'  [{tier}] {name}')

    print()
    print('=== Final comps (DOM) ===')
    for c in comps:
        print(f"  [{c['tier'] or '?'}] {c['name']} ({c['difficulty']}) - {len(c['cards'])} cards: {c['cards'][:6]}")

    browser.close()
