"""診斷 pool 比對問題：找出官方 75 vs 快取哪裡對不起來"""
import urllib.request, json, gzip, sys, re
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        try: body = gzip.decompress(body)
        except: pass
        return json.loads(body)

# 1. 抓官方 75 張
d = fetch_json('https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page=1')
pages = d.get('pageCount', 1)
all_bg = list(d.get('cards', []))
for p in range(2, pages + 1):
    d2 = fetch_json(f'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page={p}')
    all_bg.extend(d2.get('cards', []))

official_75 = [c for c in all_bg if c.get('cardTypeId') == 43]
print(f"Official count: {len(official_75)}")

# 顯示全部 75 張的 zh_TW name
official_tw = []
for c in official_75:
    name = c.get('name', {})
    tw = name.get('zh_TW', '') if isinstance(name, dict) else ''
    en = name.get('en_US', '') if isinstance(name, dict) else ''
    dbf_id = c.get('id', '')
    slug = c.get('slug', '')
    official_tw.append({'tw': tw, 'en': en, 'dbf': dbf_id, 'slug': slug})

# 統計空白或重複
tw_counts = {}
for o in official_tw:
    tw_counts[o['tw']] = tw_counts.get(o['tw'], 0) + 1

print(f"\n--- Empty zh_TW ---")
for o in official_tw:
    if not o['tw']:
        print(f"  dbf={o['dbf']} slug={o['slug']} en={o['en']}")

print(f"\n--- Duplicate zh_TW (count > 1) ---")
for tw, cnt in sorted(tw_counts.items(), key=lambda x: -x[1]):
    if cnt > 1:
        print(f"  '{tw}' x{cnt}")

# 2. 讀本地快取
import os
cache_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'bg_anomaly_cache.json')
with open(cache_path, encoding='utf-8') as f:
    cache = json.load(f)
cache_names = {a['name'] for a in cache}
print(f"\nCache size: {len(cache)}")

# 3. 比較
pool_names_set = {o['tw'] for o in official_tw if o['tw']}
print(f"Pool unique zh_TW names: {len(pool_names_set)}")

in_pool_count = sum(1 for a in cache if a['name'] in pool_names_set)
print(f"Cache entries matching pool: {in_pool_count}")

print(f"\n--- Pool names NOT in cache ---")
for tw in sorted(pool_names_set - cache_names):
    print(f"  '{tw}'")

print(f"\n--- Cache names NOT in pool (historical) ---")
for name in sorted(cache_names - pool_names_set):
    # find its ID
    for a in cache:
        if a['name'] == name:
            print(f"  {a['id']:40s} | '{name}'")
            break

# 4. Try dbfId matching
print(f"\n=== Try matching by dbfId ===")
hsjurl = 'https://api.hearthstonejson.com/v1/latest/zhTW/cards.json'
req = urllib.request.Request(hsjurl, headers=headers)
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try: raw = gzip.decompress(raw)
except: pass
all_hsj = json.loads(raw.decode('utf-8', 'ignore'))

dbf_to_name = {c.get('dbfId'): c.get('name', '') for c in all_hsj if c.get('type') == 'BATTLEGROUND_ANOMALY'}
print(f"HSJ anomaly dbfIds: {len(dbf_to_name)}")

matched_via_dbf = 0
unmatched_dbf = []
for o in official_tw:
    dbf = o['dbf']
    hsj_name = dbf_to_name.get(dbf)
    if hsj_name:
        matched_via_dbf += 1
    else:
        unmatched_dbf.append(o)

print(f"Matched via dbfId: {matched_via_dbf}/{len(official_75)}")
if unmatched_dbf:
    print(f"\nUnmatched by dbfId:")
    for o in unmatched_dbf:
        print(f"  dbf={o['dbf']} slug={o['slug']} tw={o['tw']} en={o['en']}")

# Show the dbfId-based pool names
pool_via_dbf = set()
for o in official_tw:
    hsj_name = dbf_to_name.get(o['dbf'], '')
    if hsj_name:
        pool_via_dbf.add(hsj_name)
print(f"\nPool via dbfId unique names: {len(pool_via_dbf)}")
in_pool_dbf = sum(1 for a in cache if a['name'] in pool_via_dbf)
print(f"Cache entries matching pool (dbfId method): {in_pool_dbf}")
