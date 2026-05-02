"""Get all rendered image URLs from HSReplay comps page."""
from playwright.sync_api import sync_playwright
import json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={'width':1280,'height':900}
    )
    page = ctx.new_page()

    img_urls = set()
    def on_resp(resp):
        url = resp.url
        if any(x in url for x in ['hearthstonejson', 'hsreplay', 'blizzard']) and any(x in url for x in ['.jpg', '.png', '.webp']):
            img_urls.add(url)

    page.on('response', on_resp)
    try:
        page.goto('https://hsreplay.net/battlegrounds/comps/', wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    time.sleep(15)

    # Get all img elements from DOM
    try:
        imgs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img')).map(function(i) {
                return {src: i.src, alt: i.alt || '', w: i.naturalWidth};
            }).filter(function(i) { return i.src && i.src.length > 10; });
        }""")
        print('Total img elements:', len(imgs))
        for img in imgs[:40]:
            if img['w'] > 0:
                print(f"  {img['w']}px | {img['alt'][:30]:30s} | {img['src'][:100]}")
    except Exception as e:
        print('Error:', e)

    print()
    print('Network image URLs:')
    for url in sorted(img_urls):
        if 'BG' in url or 'card' in url.lower():
            print(' ', url[:120])

    browser.close()
