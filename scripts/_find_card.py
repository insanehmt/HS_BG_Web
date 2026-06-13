"""找特定卡牌和官網 BG 法術全清單"""
import urllib.request, json, gzip

url = 'https://api.hearthstonejson.com/v1/latest/zhTW/cards.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try:
    raw = gzip.decompress(raw)
except Exception:
    pass
cards = json.loads(raw.decode('utf-8', 'ignore'))

# 搜尋名字含「哎」或「邪惡」的牌
print("=== 名字含「哎」或「邪惡」===")
for c in cards:
    name = c.get('name','')
    if '哎' in name or '邪惡' in name:
        cid = c.get('id','')
        print(f"  {cid:40s} | {name} | type={c.get('type')} | techLevel={c.get('techLevel')} | pool={c.get('isBattlegroundsPoolSpell')}")

# 也搜 yogg / Oh My
print("\n=== 名字含 yogg / Yogg ===")
for c in cards:
    name = c.get('name','')
    if 'ogg' in name.lower():
        cid = c.get('id','')
        if cid.startswith('BG') or cid.startswith('EBG'):
            print(f"  {cid:40s} | {name} | type={c.get('type')} | techLevel={c.get('techLevel')}")

# 找所有 BG pool spells 沒有 techLevel 的
print("\n=== isBattlegroundsPoolSpell=True 但沒有 techLevel（目前被過濾）===")
count = 0
for c in cards:
    cid = c.get('id','')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL','BATTLEGROUND_SPELL'):
        continue
    if not c.get('name'):
        continue
    if c.get('isBattlegroundsPoolSpell') and not c.get('techLevel'):
        count += 1
        print(f"  {cid:40s} | {c.get('name')} | pool=True | techLevel=None")
print(f"  共 {count} 張")
