import json
with open('data/bg_comps.json', encoding='utf-8') as f:
    comps = json.load(f)
print(f'Total: {len(comps)}')
for c in comps:
    tid = c.get('id','?')
    tier = c.get('tier','?')
    name = c.get('name') or c.get('original_name','?')
    print(f'  [{tier}] {tid:35s} {name}')
