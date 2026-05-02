"""Parse HSReplay - find comp names + cards together."""
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
        // Find the smallest ancestor of each group of cards that also contains a comp name
        // Strategy: find containers with 4-16 cards, then go UP until we find text with letters

        var minLinks = Array.from(document.querySelectorAll('a[href*="/battlegrounds/minions/"]'));
        var seen = new Set();
        var comps = [];

        for (var link of minLinks) {
            var el = link;
            var compEl = null;
            // Find card group container (4-16 cards)
            for (var j = 0; j < 15; j++) {
                el = el.parentElement;
                if (!el) break;
                var cnt = el.querySelectorAll('a[href*="/battlegrounds/minions/"]').length;
                if (cnt >= 4 && cnt <= 16) {
                    compEl = el;
                    break;
                }
            }
            if (!compEl || seen.has(compEl)) continue;
            seen.add(compEl);

            // Get cards
            var cards = Array.from(compEl.querySelectorAll('a[href*="/battlegrounds/minions/"]')).map(function(a) {
                var img = a.querySelector('img');
                var src = img ? img.src : '';
                var m = src.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);
                return m ? m[1] : '';
            }).filter(Boolean);

            // Walk UP from compEl to find comp name
            var nameEl = compEl;
            var compName = '';
            var difficulty = '';
            var tier = '';

            for (var k = 0; k < 10; k++) {
                nameEl = nameEl.parentElement;
                if (!nameEl) break;
                var text = nameEl.innerText || '';
                var lines = text.split('\\n').map(function(s) { return s.trim(); }).filter(Boolean);
                // Look for a line that looks like a comp name (contains letters, not just numbers)
                for (var line of lines) {
                    if (/[A-Za-z]{4,}/.test(line) && !/hearthstonejson|Copyright|navigation/.test(line)) {
                        if (line === 'S' || line === 'A' || line === 'B' || line === 'C') {
                            tier = line;
                        } else if (/Medium|Easy|Hard/.test(line)) {
                            difficulty = line;
                        } else if (line.length > 3 && line.length < 60 && !compName) {
                            compName = line;
                        }
                    }
                }
                if (compName) break;
            }

            comps.push({
                name: compName,
                tier: tier,
                difficulty: difficulty,
                cards: cards
            });
        }
        return comps;
    }""")

    print('Comps found:', len(result))
    for c in result:
        print()
        print(f"  [{c['tier']}] {c['name']} ({c['difficulty']}) - {len(c['cards'])} cards")
        print(f"  Cards: {c['cards']}")

    browser.close()
