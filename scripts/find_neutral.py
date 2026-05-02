import json

with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    minions = json.load(f)

# Find neutral / ALL-race minions
neutral = [m for m in minions if not m.get('races') or m.get('races') == [] or 'ALL' in (m.get('races') or [])]
print(f"Neutral minions: {len(neutral)}")
for m in sorted(neutral, key=lambda x: x.get('techLevel', 99)):
    races = ','.join(m.get('races') or [])
    mid = m['id']
    name = m['name']
    tl = m.get('techLevel', '?')
    print(f"  {mid:22s}  T{tl}  {races:6s}  {name}")

print("\n--- All races in cache ---")
all_races = set()
for m in minions:
    for r in (m.get('races') or []):
        all_races.add(r)
print(sorted(all_races))

# Print keyword search
print("\n--- Cards with 'ring' or 'back' in name ---")
for m in minions:
    n = m['name'].lower()
    if 'ring' in n or 'back' in n or 'brann' in n or 'discover' in n:
        mid = m['id']
        name = m['name']
        tl = m.get('techLevel','?')
        races = ','.join(m.get('races') or [])
        print(f"  {mid:22s}  T{tl}  {races:12s}  {name}")
