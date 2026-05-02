"""
Cleanup bg_comps.json: merge Chinese content from old IDs into Firestone IDs, remove duplicates.
"""
import json

DATA_PATH = 'data/bg_comps.json'

# Firestone ID → old ID (same conceptual comp, different naming)
ALIASES = {
    "demon_fodder":            "fodder_demons",
    "quilboar_smuggler":       "smuggler_quilboar",
    "pirate_bounty":           "bounty_pirates",
    "neutral_back_to_back":    "back_to_back",
    "dragon_kalecgos":         "kalecgos_dragons",
    "quilboar_avenge":         "avenge_quilboar",
    "mech_automaton":          "automaton_mechs",
    "mech_shield":             "shield_mechs",
    "murloc_scam":             "scam_murlocs",
    "naga_spellspam":          "spellspam_nagas",
    "naga_deep_blue":          "deep_blue_nagas",
    "undead_attack":           "attack_undead",
    "beast_self_damage":       "self_damage_beasts",
    "beast_stegodon":          "stegodon_beasts",
    "elemental_tier2_ballers": "tier2_ballers",
    "murloc_mrrglton":         "mrrglton_murlocs",
    "murloc_handbuff":         "handbuff_murlocs",
    "undead_end_of_turn":      "end_of_turn_undead",
    "undead_overflow":         "overflow_undead",
    # same IDs, no alias needed:
    # beast_banana, dragon_ring_bearer, elemental_shop_buff
}

with open(DATA_PATH, encoding='utf-8') as f:
    comps = json.load(f)

comp_map = {c['id']: c for c in comps}

# Set of old IDs to remove (they have a Firestone alias)
old_ids_to_remove = set(ALIASES.values())

merged = 0
removed = 0

for new_id, old_id in ALIASES.items():
    if new_id in comp_map and old_id in comp_map:
        nc = comp_map[new_id]
        oc = comp_map[old_id]
        # Keep Chinese name if new comp has English name or no name
        def _is_english(s):
            return bool(s) and all(ord(ch) < 128 for ch in s if ch.strip())
        if not nc.get('name') or _is_english(nc.get('name', '')):
            if oc.get('name') and not _is_english(oc['name']):
                nc['name'] = oc['name']
                print(f"  [name] {new_id}: '{nc.get('name')}' <- '{oc['name']}'")
        # Merge strategy/tips if new is empty
        if not nc.get('strategy') and oc.get('strategy'):
            nc['strategy'] = oc['strategy']
            print(f"  [strategy] {new_id}: copied")
        if not nc.get('tips') and oc.get('tips'):
            nc['tips'] = oc['tips']
            print(f"  [tips] {new_id}: copied")
        merged += 1
        print(f"  Merged {old_id} -> {new_id}")

# Build final list: remove old alias IDs ONLY if the corresponding new ID is in our data
final = []
actually_removed = []
for c in comps:
    cid = c['id']
    if cid in old_ids_to_remove:
        # Find which new ID maps to this old ID
        new_id = next((n for n, o in ALIASES.items() if o == cid), None)
        if new_id and new_id in comp_map:
            actually_removed.append(cid)
        else:
            # New ID not present – keep this comp under old ID
            final.append(c)
    else:
        final.append(c)

# Sort by tier then name
tier_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
final.sort(key=lambda c: (tier_order.get(c.get('tier', 'C'), 9), c.get('name', '')))

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f"\nDone: {len(comps)} -> {len(final)} comps (merged {merged}, removed {len(actually_removed)} old aliases)")
for c in final:
    print(f"  [{c.get('tier','?')}] {c['id']:35s} {c.get('name','')}")
