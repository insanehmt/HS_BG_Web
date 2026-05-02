import json

data = json.load(open('data/bg_minions_cache.json', encoding='utf-8'))
# Print all cards that mention round-end effects or "twice" effects
print("=== 回合結束/兩次觸發 cards ===")
for m in data:
    text = m.get('text','')
    if '兩次' in text or '回合結束' in text:
        print(f"{m['id']} | T{m.get('tech_level','?')} | {m['name']} | {m.get('races',[])} | {text[:100]}")

print()
print("=== All card IDs with BG26_502 area ===")
ids_near = [m for m in data if m['id'].startswith('BG26_5')]
for m in ids_near:
    print(f"{m['id']} | {m['name']} | {m.get('text','')[:80]}")
