"""
Download all BG Tavern Spells from hearthstonejson.com and save to bg_spells_cache.json
BG Tavern Spells have CARDTYPE=42 (BATTLEGROUND_SPELL) in the cards data
"""
import urllib.request, json, os

print("Downloading hearthstone cards (zh-TW)...")
url = "https://api.hearthstonejson.com/v1/latest/zhTW/cards.json"
with urllib.request.urlopen(url, timeout=60) as resp:
    all_cards = json.loads(resp.read().decode('utf-8'))

print(f"Total cards: {len(all_cards)}")

# BG Tavern Spells: id starts with "BG" and cardType == "SPELL" and set contains BG
# In the JSON, BG tavern spells tend to have:
#   "set": "BATTLEGROUNDS" or BG-related set
#   "type": "SPELL"
#   "mechanics": may include BATTLECRY or special tags
# Key filter: id starts with "BG" + type is SPELL

bg_spells = []
for card in all_cards:
    cid = card.get('id', '')
    ctype = card.get('type', '')
    cset = card.get('set', '')
    
    # BG tavern spells: id starts with BG, type is SPELL
    # Exclude collectible standard spells
    if (cid.startswith('BG') and 
        ctype == 'SPELL' and
        card.get('name') and
        # Must have a tech level (tavern tier) to be a BG tavern spell
        ('techLevel' in card or 'battlegroundsPremiumDbfId' in card or 
         cset in ('BATTLEGROUNDS', 'VANILLA') or
         any(tag in card.get('mechanics', []) for tag in ['BATTLECRY']))
       ):
        
        # Get tech level
        tech_level = card.get('techLevel', card.get('techLevelDbfId', 0))
        
        spell_entry = {
            "id": cid,
            "dbf_id": card.get('dbfId'),
            "name": card.get('name', ''),
            "text": card.get('text', ''),
            "type": "SPELL",
            "tech_level": tech_level,
            "set": cset,
            "cost": card.get('cost', 0),
            "races": card.get('races', card.get('race', [])),
        }
        bg_spells.append(spell_entry)

# Also catch spells with explicit techLevel set (most reliable filter)
bg_spells_by_tech = []
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
            "text": card.get('text', ''),
            "type": "SPELL",
            "tech_level": card.get('techLevel', 0),
            "set": card.get('set', ''),
            "cost": card.get('cost', 0),
        }
        bg_spells_by_tech.append(spell_entry)
        seen_ids.add(cid)

print(f"\nBG Spells (broad filter): {len(bg_spells)}")
print(f"BG Spells (techLevel filter): {len(bg_spells_by_tech)}")

# Use techLevel filter as primary
out = bg_spells_by_tech
out.sort(key=lambda x: (x['tech_level'], x['id']))

# Print sample
print("\nSample entries:")
for s in out[:10]:
    print(f"  {s['id']} | T{s['tech_level']} | {s['name']} | {s['text'][:60]}")

# Check for Back to Back specifically
btb = next((s for s in out if s['id'] == 'BG35_952'), None)
if btb:
    print(f"\n✅ Back to Back found: {btb}")
else:
    print("\n❌ BG35_952 not found in techLevel filter, checking broad...")
    btb2 = next((s for s in all_cards if s.get('id') == 'BG35_952'), None)
    if btb2:
        print(f"  Raw data: {btb2}")

# Save
out_path = os.path.join(os.path.dirname(__file__), "..", "data", "bg_spells_cache.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(out)} BG spells to bg_spells_cache.json")
print(f"\nAll spells:")
for s in out:
    print(f"  T{s['tech_level']} | {s['id']} | {s['name']}")
