"""
Parse ALL BG tavern spells from downloaded cards_zhtw_raw.json
Includes both SPELL (BGS_Treasures) and BATTLEGROUND_SPELL (BG35_952 style) types
"""
import json, os

print("Loading cards data...")
raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards_zhtw_raw.json")
with open(raw_path, encoding='utf-8') as f:
    all_cards = json.load(f)

print(f"Total cards: {len(all_cards)}")

bg_spells = []
seen_ids = set()

for card in all_cards:
    cid = card.get('id', '')
    ctype = card.get('type', '')
    
    # Include both SPELL (BGS_Treasures) and BATTLEGROUND_SPELL (BG35_xxx)
    is_spell_type = ctype in ('SPELL', 'BATTLEGROUND_SPELL')
    
    # Must start with BG, have a name, have a techLevel, be a spell
    if (cid.startswith('BG') and
        is_spell_type and
        card.get('techLevel') and
        card.get('name') and
        cid not in seen_ids):
        
        spell_entry = {
            "id": cid,
            "dbf_id": card.get('dbfId'),
            "name": card.get('name', ''),
            "text": card.get('text', '').replace('\n', ' '),
            "type": ctype,
            "tech_level": card.get('techLevel', 0),
            "set": card.get('set', ''),
            "cost": card.get('cost', 0),
        }
        bg_spells.append(spell_entry)
        seen_ids.add(cid)

bg_spells.sort(key=lambda x: (x['tech_level'], x['id']))

print(f"\nFound {len(bg_spells)} BG tavern spells total")

# Check Back to Back
btb = next((s for s in bg_spells if s['id'] == 'BG35_952'), None)
if btb:
    print(f"✅ BG35_952: {btb['name']} | T{btb['tech_level']} | {btb['text'][:80]}")

print("\nAll BG spells:")
for s in bg_spells:
    print(f"  T{s['tech_level']} | {s['id']} | {s['name']} | {s['text'][:70]}")

# Save
out_path = os.path.join(os.path.dirname(__file__), "..", "data", "bg_spells_cache.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(bg_spells, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(bg_spells)} spells to bg_spells_cache.json")
# Delete raw file to save space
os.remove(raw_path)
print("Deleted raw cards file.")
