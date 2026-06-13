"""找出官方 API 的 anomaly type 值"""
import urllib.request, json, gzip, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        try: body = gzip.decompress(body)
        except: pass
        return json.loads(body)

# Get first page
d = fetch('https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page=1')
cards = d.get('cards', [])
total = d.get('cardCount', 0)
pages = d.get('pageCount', 0)
print(f"Total: {total}, Pages: {pages}")

# Get all pages
all_cards = list(cards)
for p in range(2, pages + 1):
    d2 = fetch(f'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page={p}')
    all_cards.extend(d2.get('cards', []))
    print(f"  Page {p}: +{len(d2.get('cards',[]))} cards")

print(f"\nTotal fetched: {len(all_cards)}")

# Check all card types
types = {}
for c in all_cards:
    t = c.get('cardTypeId', c.get('type', '?'))
    types[t] = types.get(t, 0) + 1
print(f"\nCard types: {types}")

# Find anomaly-like cards
print("\n=== Cards with 'anomal' in any field ===")
anomaly_cards = []
for c in all_cards:
    name = c.get('name', '')
    slug = str(c.get('slug', ''))
    ctype = str(c.get('cardTypeId', c.get('type', '')))
    if 'anomal' in slug.lower() or 'anomal' in ctype.lower():
        anomaly_cards.append(c)

print(f"Found {len(anomaly_cards)} anomaly cards via slug/type")
if anomaly_cards:
    print(f"First card keys: {list(anomaly_cards[0].keys())}")
    for c in anomaly_cards[:3]:
        print(f"  {c.get('slug','?')} | {c.get('name','?')} | type={c.get('cardTypeId','?')}")

# Check if there's a cardTypeId for anomalies
print("\n=== All unique cardTypeIds ===")
type_ids = {}
for c in all_cards:
    tid = c.get('cardTypeId', '?')
    if tid not in type_ids:
        type_ids[tid] = c.get('name', '?')
for tid, ex in sorted(type_ids.items(), key=lambda x: str(x[0])):
    print(f"  typeId={tid}: e.g. {ex}")
