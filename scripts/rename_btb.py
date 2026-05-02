import json, os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bg_comps.json")
with open(DATA_PATH, encoding='utf-8') as f:
    comps = json.load(f)

for c in comps:
    if c['id'] == 'back_to_back':
        c['name'] = "背靠背法術疊加流"
        print(f"Renamed to: {c['name']}")
        break

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(comps, f, ensure_ascii=False, indent=2)
print("Done.")
