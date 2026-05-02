import json
with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    m = json.load(f)

# Find all 球手 (baller) cards
print("=== All 球手 (Baller) cards ===")
for c in m:
    if '球手' in c['name'] or '球手' in c.get('text',''):
        races = ','.join(c.get('races') or [])
        print(f"{c['id']:22s}  T{c.get('tech_level','?')}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
        print(f"   TEXT: {c.get('text','')[:200]}")

# Find cards that attack multiple times or have cleave
print("\n=== Cards with 'windfury' or '風怒' or '清除' or 'cleave' or multiple attacks ===")
for c in m:
    txt = c.get('text','')
    mechs = c.get('mechanics', [])
    name = c['name']
    if any(k in txt or k in name for k in ['風怒','再次攻擊','攻擊兩次','攻擊三次','橫掃']) or \
       any(k in mechs for k in ['WINDFURY','MEGA_WINDFURY']):
        races = ','.join(c.get('races') or [])
        print(f"{c['id']:22s}  T{c.get('tech_level','?')}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
        print(f"   TEXT: {txt[:120]}")

# Ring specific - anything with 刺眼 or 戒指
print("\n=== Ring / Divine shield related ===")
for c in m:
    txt = c.get('text','')
    if '刺眼' in txt or '戒指' in txt or '聖盾' in c.get('mechanics',[]) or '聖盾' in txt:
        races = ','.join(c.get('races') or [])
        print(f"{c['id']:22s}  T{c.get('tech_level','?')}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
        print(f"   TEXT: {txt[:120]}")
