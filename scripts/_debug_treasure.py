"""找出5張寶藏庫的詳細資料"""
import urllib.request, json, gzip, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        try: body = gzip.decompress(body)
        except: pass
        return json.loads(body)

# 官方 API - 抓 75 張
all_bg = []
d = fetch_json('https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page=1')
pages = d.get('pageCount', 1)
all_bg = list(d.get('cards', []))
for p in range(2, pages + 1):
    all_bg.extend(fetch_json(f'https://hearthstone.blizzard.com/en-us/api/cards?gameMode=battlegrounds&pageSize=200&page={p}').get('cards', []))

official_75 = [c for c in all_bg if c.get('cardTypeId') == 43]
treasure_5 = [c for c in official_75 if isinstance(c.get('name'), dict) and c['name'].get('zh_TW') == '寶藏庫']
print(f"官方 '寶藏庫' 共 {len(treasure_5)} 張：")
for c in treasure_5:
    print(f"  dbfId={c.get('id')} slug={c.get('slug')} name={c.get('name')}")

# hearthstonejson
print("\n載入 hearthstonejson...")
req = urllib.request.Request('https://api.hearthstonejson.com/v1/latest/zhTW/cards.json', headers=headers)
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try: raw = gzip.decompress(raw)
except: pass
all_hsj = json.loads(raw.decode('utf-8', 'ignore'))

# 所有 name='寶藏庫' 且 type=BATTLEGROUND_ANOMALY
treasures_hsj = [c for c in all_hsj if c.get('name') == '寶藏庫' and c.get('type') == 'BATTLEGROUND_ANOMALY']
print(f"\nhearthstonejson '寶藏庫' BATTLEGROUND_ANOMALY: {len(treasures_hsj)} 張")
for c in treasures_hsj:
    print(f"  id={c.get('id')} dbfId={c.get('dbfId')} text={c.get('text','')[:50]}")

# dbfId 比對
official_dbfs = {c.get('id') for c in treasure_5}
print(f"\n官方 dbfIds: {official_dbfs}")
hsj_dbfs = {c.get('dbfId') for c in treasures_hsj}
print(f"HSJ dbfIds: {hsj_dbfs}")
print(f"交集: {official_dbfs & hsj_dbfs}")
print(f"官方有但 HSJ 沒有: {official_dbfs - hsj_dbfs}")
