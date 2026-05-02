"""Parse HSReplay using stable class names found in source."""
from playwright.sync_api import sync_playwright
import json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={'width':1280,'height':900}
    )
    page = ctx.new_page()

    # Capture rendered HTML
    html_store = {}
    def on_resp(resp):
        url = resp.url
        if 'hsreplay.net/battlegrounds/comps' in url and 'hgi=1' in url:
            try:
                html_store['html'] = resp.body().decode('utf-8', 'ignore')
            except Exception:
                pass

    page.on('response', on_resp)
    try:
        page.goto('https://hsreplay.net/battlegrounds/comps/', wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    time.sleep(15)

    # Parse the rendered HTML directly
    html = html_store.get('html', '')

    # Find all "board-minion" cards with their hrefs and images
    # Pattern: class="board-minion..." href="/battlegrounds/minions/CARD_ID/"
    card_pattern = re.compile(
        r'href="/battlegrounds/minions/([^/"]+)/"[^>]*>.*?'
        r'(?:alt="([^"]*)"[^>]*src="([^"]*)")'
        r'|'
        r'src="https://art\.hearthstonejson\.com[^"]*?/([A-Z][A-Z0-9_]+)\.(png|webp)"[^>]*alt="([^"]*)"',
        re.DOTALL
    )

    # Simpler: just extract from HTML in order
    # Find pattern: href="/battlegrounds/minions/SLUG/" ... img src="...CARD_ID.webp" alt="CARD NAME"
    links = re.findall(
        r'href="/battlegrounds/minions/([^/"]+)/"',
        html
    )
    print('Minion links found:', len(links))
    print(links[:10])

    # Find comp sections using tier text
    # The page structure is: tier label (S/A/B/C) -> comp rows
    # Each row has: comp name, description, difficulty, core cards

    # Find comp names from the body text we got earlier
    # Let's parse the structured text
    result = page.evaluate("""() => {
        // Get all elements that have href for minions
        var minLinks = document.querySelectorAll('a[href*="/battlegrounds/minions/"]');
        console.log('Total minion links:', minLinks.length);

        var data = [];
        for (var a of minLinks) {
            var href = a.href;
            var slug = href.match(/\\/battlegrounds\\/minions\\/([^/]+)/);
            if (!slug) continue;
            var img = a.querySelector('img');
            var imgSrc = img ? img.src : '';
            var imgAlt = img ? (img.alt || '') : '';
            var cardIdFromSrc = imgSrc.match(/\\/([A-Z][A-Z0-9_]+)\\.(png|webp)$/);

            data.push({
                slug: slug[1],
                cardId: cardIdFromSrc ? cardIdFromSrc[1] : '',
                name: imgAlt,
            });
        }
        return data;
    }""")

    print()
    print('Minion links from DOM:', len(result))
    for r in result[:20]:
        print(f"  slug={r['slug']:30s} cardId={r['cardId']:15s} name={r['name']}")

    # Now get comp groupings using the page's visual structure
    result2 = page.evaluate("""() => {
        // Find tier headers and comp rows
        var allEls = Array.from(document.querySelectorAll('*'));
        var tierPattern = /^[SABC]$/;

        var tiers = [];
        for (var el of allEls) {
            var t = (el.innerText || '').trim();
            if (tierPattern.test(t) && el.children.length === 0) {
                tiers.push({el: el, tier: t});
            }
        }
        return {tierCount: tiers.length};
    }""")
    print('Tier elements found:', result2)

    browser.close()
