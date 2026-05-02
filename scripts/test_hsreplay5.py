"""Parse HSReplay comps page - full structured data extraction."""
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

    # Extract full comp structure via JS DOM parsing
    result = page.evaluate("""() => {
        var comps = [];

        // Find all rows in the table
        var rows = document.querySelectorAll('tr, [class*="row"], [class*="Row"]');

        for (var row of rows) {
            var text = row.innerText || '';
            if (!text.trim()) continue;

            // Get images (card IDs from URLs)
            var imgs = row.querySelectorAll('img');
            var cards = [];
            for (var img of imgs) {
                var src = img.src || img.getAttribute('src') || '';
                var alt = img.alt || img.getAttribute('alt') || '';
                // Extract card ID from URL pattern like .../256x/BG12_345.png or .../256x/BG12_345.webp
                var m = src.match(/\\/([A-Z_][A-Z0-9_]+)\\.(png|jpg|webp)$/i);
                if (m) {
                    cards.push({id: m[1], name: alt});
                }
            }
            if (cards.length === 0) continue;

            // Try to find tier badge
            var tierEl = row.querySelector('[class*="tier-badge"], [class*="TierBadge"], [class*="tier-S"], [class*="tier-A"], [class*="tier-B"], [class*="tier-C"]');
            var tier = '';
            if (tierEl) {
                tier = tierEl.innerText.trim();
            }

            comps.push({
                text: text.substring(0, 200).replace(/\\n/g, ' | '),
                tier: tier,
                cards: cards
            });
        }
        return comps;
    }""")

    print('Raw rows with cards:', len(result))
    for r in result[:5]:
        print()
        print('TEXT:', r['text'][:150])
        print('TIER:', r['tier'])
        print('CARDS:', [(c['id'], c['name'][:20]) for c in r['cards'][:8]])

    # More targeted approach - get the actual comp list
    result2 = page.evaluate("""() => {
        // Look for the main comp list container
        var allText = document.body.innerHTML;
        // Find all unique BG card IDs with their surrounding context
        var matches = [];
        var re = /256x\\/([A-Z_][A-Z0-9_]+)\\.(png|webp)/g;
        var m;
        var seen = new Set();
        while ((m = re.exec(allText)) !== null) {
            if (!seen.has(m[1])) {
                seen.add(m[1]);
                // Get surrounding HTML to find comp name
                var start = Math.max(0, m.index - 500);
                var ctx = allText.substring(start, m.index + 100);
                matches.push({id: m[1], ctx: ctx.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim().substring(0, 100)});
            }
        }
        return matches;
    }""")

    print()
    print('All card IDs in order:')
    for r in result2:
        print(f"  {r['id']:20s} | context: {r['ctx'][-60:]}")

    browser.close()
