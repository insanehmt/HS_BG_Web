"""Parse HSReplay - find comp groupings by DOM traversal."""
from playwright.sync_api import sync_playwright
import json, time

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
        // Get all minion links
        var minLinks = Array.from(document.querySelectorAll('a[href*="/battlegrounds/minions/"]'));

        // For first link, walk up the DOM and print hierarchy
        if (minLinks.length === 0) return {error: 'no links'};

        var firstLink = minLinks[0];
        var hierarchy = [];
        var el = firstLink;
        for (var i = 0; i < 15; i++) {
            el = el.parentElement;
            if (!el) break;
            var cls = el.className || '';
            var tag = el.tagName;
            var childLinks = el.querySelectorAll('a[href*="/battlegrounds/minions/"]').length;
            hierarchy.push({
                tag: tag,
                cls: cls.substring(0, 60),
                childLinks: childLinks
            });
        }

        // Find the level that best groups cards per comp
        // Looking for elements that have ~4-12 minion links but not ALL 79
        var comps = [];
        var seen = new Set();
        for (var link of minLinks) {
            var el2 = link;
            var compEl = null;
            for (var j = 0; j < 15; j++) {
                el2 = el2.parentElement;
                if (!el2) break;
                var cnt = el2.querySelectorAll('a[href*="/battlegrounds/minions/"]').length;
                if (cnt >= 4 && cnt <= 16 && cnt !== 79) {
                    compEl = el2;
                    break;
                }
            }
            if (compEl && !seen.has(compEl)) {
                seen.add(compEl);
                var cards = Array.from(compEl.querySelectorAll('a[href*="/battlegrounds/minions/"]')).map(function(a) {
                    var img = a.querySelector('img');
                    var src = img ? img.src : '';
                    var m = src.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);
                    return {
                        cardId: m ? m[1] : '',
                        name: img ? img.alt : ''
                    };
                });
                var text = compEl.innerText.replace(/\\n/g, ' | ').substring(0, 200);
                comps.push({text: text, cards: cards});
            }
        }

        return {hierarchy: hierarchy, comps: comps};
    }""")

    print('=== Parent hierarchy of first card ===')
    for h in result.get('hierarchy', []):
        print(f"  {h['tag']:10s} childLinks={h['childLinks']:3d} cls={h['cls'][:50]}")

    print()
    print('=== Comps found:', len(result.get('comps', [])))
    for c in result.get('comps', []):
        print()
        print('  text:', c['text'][:120])
        print('  cards:', [(x['cardId'], x['name'][:15]) for x in c['cards'][:6]])

    browser.close()
