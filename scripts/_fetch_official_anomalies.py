"""抓取官方 75 張 BG 變異，並與 hearthstonejson 比對"""
import urllib.request, json, gzip, re, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        try: body = gzip.decompress(body)
        except: pass
        return json.loads(body)

# Fetch all BG cards across pages, filter cardTypeId=43
def fetch_all_bg():
    d = fetch('https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page=1')
    cards = list(d.get('cards', []))
    pages = d.get('pageCount', 1)
    for p in range(2, pages + 1):
        d2 = fetch(f'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page={p}')
        cards.extend(d2.get('cards', []))
    return cards

all_bg = fetch_all_bg()
official = [c for c in all_bg if c.get('cardTypeId') == 43]
print(f"Official anomaly count: {len(official)}")

# Extract zh_TW names and slugs
official_names_tw = set()
official_names_en = set()
slug_map = {}
for c in official:
    name = c.get('name', {})
    tw = name.get('zh_TW', '') if isinstance(name, dict) else ''
    en = name.get('en_US', '') if isinstance(name, dict) else ''
    slug = c.get('slug', '')
    if tw: official_names_tw.add(tw)
    if en: official_names_en.add(en)
    slug_map[slug] = {'tw': tw, 'en': en}

print(f"\nzh_TW names ({len(official_names_tw)}): {sorted(official_names_tw)[:5]}...")
print(f"en_US names ({len(official_names_en)}): {sorted(official_names_en)[:5]}...")

# Load hearthstonejson
hsjurl = 'https://api.hearthstonejson.com/v1/latest/zhTW/cards.json'
req = urllib.request.Request(hsjurl, headers=headers)
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try: raw = gzip.decompress(raw)
except: pass
all_cards = json.loads(raw.decode('utf-8', 'ignore'))

# Match by name
print(f"\n=== Matching official 75 to hearthstonejson ===")
matched = []
unmatched = []
for c in official:
    name = c.get('name', {})
    tw = name.get('zh_TW', '') if isinstance(name, dict) else ''
    en = name.get('en_US', '') if isinstance(name, dict) else ''
    # Find in hearthstonejson by tw name
    found = None
    for hc in all_cards:
        if hc.get('type') != 'BATTLEGROUND_ANOMALY':
            continue
        if hc.get('name') == tw:
            found = hc
            break
    if found:
        matched.append((tw, found.get('id')))
    else:
        unmatched.append((tw, en, c.get('slug')))

print(f"Matched: {len(matched)}/{len(official)}")
print(f"\nMatched card IDs:")
for name, cid in sorted(matched):
    print(f"  {cid:40s} | {name}")

if unmatched:
    print(f"\nUnmatched ({len(unmatched)}):")
    for tw, en, slug in unmatched:
        print(f"  {slug} | tw={tw} | en={en}")
