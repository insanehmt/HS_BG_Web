"""Extract HSReplay comps data from page."""
from playwright.sync_api import sync_playwright
import gzip, json, time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={'width':1280,'height':900}
    )
    page = ctx.new_page()

    html_content = {}
    def on_resp(resp):
        url = resp.url
        if 'hsreplay.net/battlegrounds/comps' in url and 'hgi=1' in url:
            try:
                body = resp.body()
                html_content['html'] = body.decode('utf-8', 'ignore')
            except Exception:
                pass
        if 'battlegrounds_comps' in url and '.js' in url:
            try:
                body = resp.body()
                html_content['js'] = body.decode('utf-8', 'ignore')
            except Exception:
                pass

    page.on('response', on_resp)
    try:
        page.goto('https://hsreplay.net/battlegrounds/comps/', wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    time.sleep(12)

    # Check HTML for embedded data
    html = html_content.get('html', '')
    print('HTML size:', len(html))

    # Look for JSON data
    for kw in ['"comps"', '"compositions"', '"archetypes"', 'INITIAL_STATE', 'Initial']:
        idx = html.find(kw)
        if idx >= 0:
            print(f'Found {kw!r} at pos {idx}:')
            print(html[max(0,idx-20):idx+200])
            print()

    # Try JS evaluation to get rendered content
    try:
        data = page.evaluate("""() => {
            var result = {};
            result.bodyPreview = document.body.innerText.substring(0, 3000);
            return result;
        }""")
        print()
        print('Body text:')
        print(data.get('bodyPreview', '')[:2000])
    except Exception as e:
        print('JS eval error:', e)

    browser.close()
