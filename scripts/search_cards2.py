import json
with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    m = json.load(f)

print(f"Total: {len(m)} cards")

# tech_level distribution
for tl in range(1, 8):
    cards_tl = [c for c in m if c.get('tech_level') == tl]
    print(f"T{tl}: {len(cards_tl)} cards")

# Ring bearer details
print("\n=== BG34_921 ===")
for c in m:
    if c['id'] == 'BG34_921':
        print(c)

# Search card texts for back-to-back type mechanics
print("\n=== Cards with '連續' or '相同' or '接連' in text ===")
for c in m:
    txt = c.get('text','')
    if any(k in txt for k in ['連續','接連','相同類型','緊接','之後','一個接一個']):
        races = ','.join(c.get('races') or [])
        print(f"{c['id']:22s}  T{c.get('tech_level','?')}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
        print(f"   TEXT: {txt[:120]}")

# Find T2 powerhouses
print("\n=== T2 cards with high stats or strong effects ===")
t2 = [c for c in m if c.get('tech_level') == 2]
for c in sorted(t2, key=lambda x: x.get('attack',0)+x.get('health',0), reverse=True)[:20]:
    races = ','.join(c.get('races') or [])
    print(f"{c['id']:22s}  {races:15s}  {c['attack']}/{c['health']}  {c['name']}")
    if c.get('text'):
        print(f"   TEXT: {c['text'][:100]}")
