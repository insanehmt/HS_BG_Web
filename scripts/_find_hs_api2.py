"""深度探測官方 HS 卡牌庫 API"""
import urllib.request, json, re, gzip

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Referer': 'https://hearthstone.blizzard.com/zh-tw/cards',
}

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            try: body = gzip.decompress(body)
            except: pass
            ct = r.headers.get('Content-Type', '')
            if 'json' in ct:
                return json.loads(body)
            return body.decode('utf-8', 'ignore')
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Try different parameter combos for anomaly cards
tests = [
    'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&type=battleground_anomaly&pageSize=200&locale=en_US',
    'https://hearthstone.blizzard.com/zh-tw/api/cards?gameMode=battlegrounds&type=battleground_anomaly&pageSize=200',
    'https://hearthstone.blizzard.com/en-us/api/cards?set=battlegrounds&keyword=anomaly&pageSize=200',
    'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200',
    'https://hearthstone.blizzard.com/en-us/api/cards?set=battlegrounds&pageSize=50&page=1',
]
for url in tests:
    print(f"\n{url}")
    r = fetch(url)
    if isinstance(r, dict):
        count = r.get('cardCount', 0)
        cards = r.get('cards', [])
        print(f"  cardCount={count} | cards_len={len(cards)} | pageCount={r.get('pageCount')}")
        if cards:
            print(f"  First 3: {[c.get('name','?') for c in cards[:3]]}")

# Examine HS website HTML for API patterns
print("\n=== Extracting API patterns from HTML ===")
html_url = 'https://hearthstone.blizzard.com/en-us/cards'
req = urllib.request.Request(html_url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', 'ignore')
    # Find API patterns
    patterns = re.findall(r'["\'](/[a-z-]+/api/cards[^"\']*)["\']', html)
    for p in patterns[:10]:
        print(f"  {p}")
    # Find any fetch/axios calls
    fetches = re.findall(r'fetch\(["\']([^"\']+)["\']', html)
    for f in fetches[:5]:
        print(f"  fetch: {f}")
    # JS bundle URLs
    scripts = re.findall(r'src="(/[^"]+\.js[^"]*)"', html)
    print(f"\n  Script bundles: {scripts[:5]}")
except Exception as e:
    print(f"  HTML error: {e}")
