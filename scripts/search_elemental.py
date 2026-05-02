import json
with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    m = json.load(f)

# Find all ELEMENTAL cards for baller support
print("=== ELEMENTAL cards ===")
elems = [c for c in m if 'ELEMENTAL' in (c.get('races') or [])]
for c in sorted(elems, key=lambda x: x.get('tech_level', 99)):
    tl = c.get('tech_level','?')
    races = ','.join(c.get('races') or [])
    print(f"T{tl}  {c['id']:22s}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
    txt = c.get('text','').replace('\n',' ')
    if txt:
        print(f"      {txt[:130]}")
