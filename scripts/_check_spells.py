"""診斷：找出被過濾掉的手下產生法術 + 分類錯誤的時光扭曲法術"""
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

print("=== 時光扭曲 + HeroPowerSpell（目前被誤判為手下產生）===")
for c in cards:
    cid = c.get('id', '')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL', 'BATTLEGROUND_SPELL'):
        continue
    if 'HeroPowerSpell' in cid and c.get('battlegroundsTimewarpCard'):
        print(f"  {cid} | {c.get('name')} | timewarp={c.get('battlegroundsTimewarpCard')} | techLevel={c.get('techLevel')}")

print()
print("=== 無 techLevel 但有 battlegroundsRelatedCard（手下產生法術，目前被過濾）===")
count = 0
for c in cards:
    cid = c.get('id', '')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL', 'BATTLEGROUND_SPELL'):
        continue
    if not c.get('name'):
        continue
    if not c.get('techLevel') and c.get('battlegroundsRelatedCard'):
        count += 1
        print(f"  {cid} | {c.get('name')} | related={c.get('battlegroundsRelatedCard')} | pool={c.get('isBattlegroundsPoolSpell')}")
print(f"  共 {count} 張")

print()
print("=== 無 techLevel、無 related、但 in_pool=True 的法術（也被過濾）===")
for c in cards:
    cid = c.get('id', '')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL', 'BATTLEGROUND_SPELL'):
        continue
    if not c.get('name'):
        continue
    if not c.get('techLevel') and not c.get('battlegroundsRelatedCard') and c.get('isBattlegroundsPoolSpell'):
        print(f"  {cid} | {c.get('name')} | pool=True")
