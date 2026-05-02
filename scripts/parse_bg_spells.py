"""
Parse BG tavern spells from downloaded cards_zhtw_raw.json
"""
import json, os

print("Loading cards data...")
raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards_zhtw_raw.json")
with open(raw_path, encoding='utf-8') as f:
    all_cards = json.load(f)

print(f"Total cards: {len(all_cards)}")

# BG Tavern Spells: id starts with "BG", type is SPELL, has techLevel
bg_spells = []
seen_ids = set()

for card in all_cards:
    cid = card.get('id', '')
    ctype = card.get('type', '')
    
    if (cid.startswith('BG') and 
        ctype == 'SPELL' and 
        card.get('techLevel') and
        card.get('name') and
        cid not in seen_ids):
        
        spell_entry = {
            "id": cid,
            "dbf_id": card.get('dbfId'),
            "name": card.get('name', ''),
            "text": card.get('text', '').replace('\n', ' '),
            "type": "SPELL",
            "tech_level": card.get('techLevel', 0),
            "set": card.get('set', ''),
            "cost": card.get('cost', 0),
        }
        bg_spells.append(spell_entry)
        seen_ids.add(cid)

bg_spells.sort(key=lambda x: (x['tech_level'], x['id']))

print(f"\nFound {len(bg_spells)} BG tavern spells")

# Check for Back to Back
btb = next((s for s in bg_spells if s['id'] == 'BG35_952'), None)
if btb:
    print(f"✅ BG35_952: {btb['name']} | T{btb['tech_level']} | {btb['text'][:80]}")
else:
    # Search more broadly
    print("BG35_952 not found with techLevel filter, searching raw...")
    raw = next((c for c in all_cards if c.get('id') == 'BG35_952'), None)
    if raw:
        print(f"  Found in raw: {raw.get('name')} | type={raw.get('type')} | techLevel={raw.get('techLevel')}")
        print(f"  Full raw keys: {list(raw.keys())}")

print("\nAll BG spells by tier:")
for s in bg_spells:
    print(f"  T{s['tech_level']} | {s['id']} | {s['name']} | {s['text'][:70]}")

# Save
out_path = os.path.join(os.path.dirname(__file__), "..", "data", "bg_spells_cache.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(bg_spells, f, ensure_ascii=False, indent=2)

print(f"\nSaved to bg_spells_cache.json")
