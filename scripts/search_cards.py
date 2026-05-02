import json
with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    m = json.load(f)

keywords = ['背靠背','連續','戒指','二費','環','ring','back','baller','tier2','t2','依序']
print("=== Keyword matches ===")
for card in m:
    n = card['name'].lower()
    mid = card['id'].lower()
    for k in keywords:
        if k.lower() in n or k.lower() in mid:
            races = ','.join(card.get('races') or [])
            atk = card.get('attack','?')
            hp = card.get('health','?')
            tl = card.get('techLevel','?')
            cid = card['id']
            cname = card['name']
            print(f"{cid:22s}  T{tl}  {races:15s}  {atk}/{hp}  {cname}")
            break

print()
print("=== Cards by techLevel count ===")
for tl in range(1,8):
    cards_tl = [c for c in m if c.get('techLevel') == tl]
    print(f"T{tl}: {len(cards_tl)}")

# Also print all T2 cards
print()
print("=== T2 cards ===")
for c in m:
    if c.get('techLevel') == 2:
        races = ','.join(c.get('races') or [])
        print(f"{c['id']:22s}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
