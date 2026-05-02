"""Parse HSReplay comps page - extract full structured data."""
from playwright.sync_api import sync_playwright
import json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={'width':1280,'height':900}
    )
    page = ctx.new_page()

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
    time.sleep(12)

    # Extract card IDs from image URLs in the HTML
    html = html_store.get('html', '')

    # Card images on HSReplay usually have card IDs in the URL
    card_img_urls = re.findall(r'(?:art\.hearthstonejson\.com|hearthstonejson\.com)[^\"\'>\s]*?([A-Z][A-Z0-9_]+)(?:\.jpg|\.png|\.webp)', html)
    print('Card IDs from img URLs:', len(card_img_urls))
    print(card_img_urls[:20])

    # Also check for data- attributes
    data_attrs = re.findall(r'data-card-id=["\']([^"\']+)["\']', html)
    print('data-card-id attrs:', len(data_attrs))
    print(data_attrs[:20])

    # Check for card ID patterns in the full HTML
    all_card_ids = re.findall(r'\b(BG[A-Z0-9_]{3,20}|BGS_\d+)\b', html)
    unique_ids = list(dict.fromkeys(all_card_ids))
    print('BG* card IDs found:', len(unique_ids))
    print(unique_ids[:30])

    # Use JS to extract the actual DOM structure
    try:
        result = page.evaluate("""() => {
            var comps = [];
            // Try various selectors
            var rows = document.querySelectorAll('[class*="comp"], [class*="Comp"], tr, .tier-row');
            rows.forEach(function(row) {
                var text = row.innerText;
                if (text && text.length > 10 && text.length < 500) {
                    // Find images with card IDs
                    var imgs = row.querySelectorAll('img');
                    var imgSrcs = Array.from(imgs).map(function(i) { return i.src || i.getAttribute('src') || ''; });
                    if (imgSrcs.length > 0) {
                        comps.push({text: text.substring(0,100), imgs: imgSrcs.slice(0,8)});
                    }
                }
            });
            return comps.slice(0, 30);
        }""")
        print()
        print('DOM comps:')
        for item in result[:10]:
            print('  text:', item['text'][:80])
            print('  imgs:', item['imgs'][:4])
            print()
    except Exception as e:
        print('JS eval error:', e)

    browser.close()
