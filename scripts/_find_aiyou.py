"""找「哎呦，全是邪惡！」和所有 BG pool spells（含非 BG 前綴）"""
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

print("=== 所有 isBattlegroundsPoolSpell=True 的法術（含非 BG 前綴）===")
pool_spells = []
for c in cards:
    cid = c.get('id','')
    if c.get('type') not in ('SPELL','BATTLEGROUND_SPELL'):
        continue
    if not c.get('isBattlegroundsPoolSpell'):
        continue
    if not c.get('name'):
        continue
    pool_spells.append(c)

pool_spells.sort(key=lambda x: x.get('id',''))
non_bg = [c for c in pool_spells if not (c.get('id','').startswith('BG') or c.get('id','').startswith('EBG_'))]

print(f"總共 {len(pool_spells)} 張，其中非 BG/EBG 前綴 {len(non_bg)} 張：")
for c in non_bg:
    print(f"  {c.get('id',''):40s} | {c.get('name','')} | techLevel={c.get('techLevel')}")

print("\n=== 所有含『哎』或『惡』字的 BG 相關法術 ===")
for c in cards:
    name = c.get('name','')
    cid = c.get('id','')
    if ('哎' in name or ('惡' in name and 'BG' in cid)):
        print(f"  {cid:40s} | {name} | type={c.get('type')} | techLevel={c.get('techLevel')} | pool={c.get('isBattlegroundsPoolSpell')}")
