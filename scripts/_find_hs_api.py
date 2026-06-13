"""探測官方 HS 卡牌庫 API，找出變異清單端點"""
import urllib.request, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get('Content-Type', '')
            body = r.read()
            print(f"  STATUS 200 | CT: {ct[:60]} | Size: {len(body)}")
            if 'json' in ct:
                return json.loads(body)
            return body.decode('utf-8', 'ignore')
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Official HS card library API candidates
candidates = [
    'https://hearthstone.blizzard.com/en-us/api/cards?set=BATTLEGROUNDS&type=battleground_anomaly&pageSize=100',
    'https://hearthstone.blizzard.com/en-us/api/cards?set=battlegrounds&type=anomaly&pageSize=100',
    'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&type=anomaly&pageSize=100',
    'https://hearthstone.blizzard.com/en-us/cards?set=battlegrounds',
    'https://api.blizzard.com/hearthstone/cards?locale=en_US&set=battlegrounds&type=anomaly',
]

for url in candidates:
    print(f"\n{url}")
    result = fetch(url)
    if isinstance(result, dict):
        print(f"  Keys: {list(result.keys())[:8]}")
        cards = result.get('cards', result.get('results', []))
        if cards:
            print(f"  Found {len(cards)} cards")
            print(f"  First: {cards[0].get('name','?')} | id={cards[0].get('id','?')}")
    elif isinstance(result, str) and len(result) > 100:
        # Look for JSON API calls in HTML
        api_calls = re.findall(r'https?://[^"\']+/api/cards[^"\']*', result)
        if api_calls:
            print(f"  Found API calls in HTML: {api_calls[:3]}")
        print(f"  HTML preview: {result[:200]}")
