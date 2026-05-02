"""Parse HSReplay comps - extract comp name + card IDs via DOM traversal."""
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
        var comps = [];
        var currentTier = '';

        // The page has rows. Each row has the comp data.
        // Look for links with /battlegrounds/minions/ pattern to find card IDs
        // and group them by their parent container

        // Find all comp containers - they contain card links
        var allLinks = Array.from(document.querySelectorAll('a[href*="/battlegrounds/minions/"]'));
        console.log('minion links:', allLinks.length);

        // Group by closest tr or comp container
        var compContainers = new Map();
        for (var link of allLinks) {
            // Walk up to find the comp container (a tr or div that contains multiple cards)
            var el = link;
            for (var i = 0; i < 8; i++) {
                el = el.parentElement;
                if (!el) break;
                var tag = el.tagName;
                if (tag === 'TR' || (el.className && (el.className.includes('row') || el.className.includes('Row') || el.className.includes('comp')))) {
                    var key = el;
                    if (!compContainers.has(key)) compContainers.set(key, []);
                    compContainers.get(key).push(link);
                    break;
                }
            }
        }

        for (var [container, links] of compContainers) {
            var cardIds = [];
            var cardNames = [];
            for (var l of links) {
                var href = l.href || '';
                var m = href.match(/\\/battlegrounds\\/minions\\/([^/]+)/);
                if (m) {
                    cardIds.push(m[1]);
                    // Find card name from img alt or text
                    var img = l.querySelector('img');
                    cardNames.push(img ? (img.alt || img.getAttribute('alt') || '') : '');
                }
            }

            // Get tier and comp name from the row
            var rowText = container.innerText || '';
            // Find img card IDs from src in this container  
            var imgSrcs = Array.from(container.querySelectorAll('img')).map(function(i) {
                var src = i.src || '';
                var m2 = src.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);
                return m2 ? {id: m2[1], name: i.alt || ''} : null;
            }).filter(Boolean);

            comps.push({
                text: rowText.replace(/\\n/g, ' | ').substring(0, 200),
                cardIds: cardIds,
                cardNames: cardNames,
                imgCards: imgSrcs,
            });
        }

        // Also try getting the page's text structure with tier labels
        var bodyText = document.body.innerText;
        return {comps: comps, bodyText: bodyText.substring(0, 5000)};
    }""")

    comps = result['comps']
    print('Comps found:', len(comps))
    for c in comps:
        print()
        print('TEXT:', c['text'][:150])
        print('cardIds:', c['cardIds'])
        print('imgCards:', [(x['id'], x['name'][:15]) for x in c['imgCards'][:8]])

    browser.close()
