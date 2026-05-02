"""Final HSReplay scraper with scrolling to load all comps."""
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
    time.sleep(8)

    # Scroll through page to trigger lazy loading
    for scroll_y in range(0, 8000, 600):
        page.evaluate(f"window.scrollTo(0, {scroll_y})")
        time.sleep(0.5)
    time.sleep(3)
    # Scroll back to trigger all renders
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(2)

    def extract_comps(pg):
        return pg.evaluate("""() => {
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
                    if (cnt >= 3 && cnt <= 20) { compEl = el; break; }
                }
                if (!compEl || seen.has(compEl)) continue;
                seen.add(compEl);
                var cards = Array.from(compEl.querySelectorAll('a[href*="/battlegrounds/minions/"]')).map(function(a) {
                    var img = a.querySelector('img');
                    var src = img ? img.src : '';
                    var m = src.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);
                    return m ? m[1] : '';
                }).filter(Boolean);
                var nameEl = compEl;
                var compName = '', difficulty = '', tier = '';
                for (var k = 0; k < 12; k++) {
                    nameEl = nameEl.parentElement;
                    if (!nameEl) break;
                    var text = nameEl.innerText || '';
                    var lines = text.split('\\n').map(function(s){return s.trim();}).filter(Boolean);
                    for (var line of lines) {
                        if ((line==='S'||line==='A'||line==='B'||line==='C') && !tier) tier=line;
                        if (/^(Medium|Easy|Hard)$/.test(line) && !difficulty) difficulty=line;
                        if (/[A-Za-z]{4,}/.test(line) && !/(Medium|Easy|Hard|hearthstone|Comps|Heroes|Guides|Season|Tier7|HSReplay|Social|Download|Copyright|navigation|Battlegrounds|Sign|Match|Last|Powered|JeefHS|Scale|Summon|Make|Buy|Spend|Play|Cast|Cycle|Overflow|Bounce|Stack|Build|Standard|Meta|Arena|Rank|English|Patch|Updated|Win|Core|Minions|Tier|Comp|Difficulty)/.test(line) && !compName && line.length>4 && line.length<65) {
                            compName = line;
                        }
                    }
                    if (compName && tier) break;
                }
                if (cards.length > 0) comps.push({name: compName, tier: tier, difficulty: difficulty, cards: cards});
            }
            return comps;
        }""")

    comps = extract_comps(page)
    print(f'Total comps: {len(comps)}')
    for c in comps:
        print(f"  [{c['tier'] or '?'}] {c['name']} ({c['difficulty']}) - {len(c['cards'])} cards")

    # Print all card IDs for each comp
    print()
    print('Full card data:')
    for c in comps:
        print(f"\n[{c['tier']}] {c['name']}")
        print(f"  {c['cards']}")

    browser.close()
