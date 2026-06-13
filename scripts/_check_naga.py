"""找 BG 納迦法術和所有手下生成法術"""
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

# 建立 id->name 對照
id2name = {c.get('id',''): c.get('name','') for c in cards}

print("=== 所有 BG 法術（含 techLevel，有 name）===")
for c in cards:
    cid = c.get('id', '')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL', 'BATTLEGROUND_SPELL'):
        continue
    if not c.get('name'):
        continue
    if not c.get('techLevel'):
        continue
    related = c.get('battlegroundsRelatedCard', '')
    timewarp = c.get('battlegroundsTimewarpCard', False)
    in_pool = c.get('isBattlegroundsPoolSpell', False)
    category_hint = ""
    if cid.startswith("BGS_Treasures"): category_hint = "暗月獎品"
    elif cid.startswith("BGDUO"): category_hint = "雙人模式"
    elif timewarp and "HeroPowerSpell" in cid: category_hint = "[應為時光扭曲,但被誤判手下產生]"
    elif timewarp or cid.startswith("BG34_Treasure"): category_hint = "時光扭曲"
    elif "HeroPowerSpell" in cid: category_hint = "手下產生(HeroPowerSpell)"
    elif in_pool: category_hint = "一般"
    elif related: category_hint = f"手下產生(related={id2name.get(related, related)})"
    else: category_hint = "已移除"
    print(f"  {cid:40s} | {c.get('name'):20s} | {category_hint}")

print()
print("=== 有 battlegroundsRelatedCard（無論 techLevel）===")
for c in cards:
    cid = c.get('id', '')
    if not (cid.startswith('BG') or cid.startswith('EBG_')):
        continue
    if c.get('type') not in ('SPELL', 'BATTLEGROUND_SPELL'):
        continue
    if not c.get('battlegroundsRelatedCard'):
        continue
    print(f"  {cid:40s} | {c.get('name','')} | techLevel={c.get('techLevel')} | related={c.get('battlegroundsRelatedCard')}")
