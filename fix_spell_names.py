"""One-time fix: replace card IDs stored in core_names/addon_names with Chinese names."""
import json, os, re

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_name_map():
    name_map = {}
    for fname in ("bg_minions_cache.json", "bg_spells_cache.json",
                  "bg_trinkets_cache.json", "bg_anomaly_cache.json"):
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for card in json.load(f):
                cid = card.get("id", "")
                nm  = card.get("name", "")
                if cid and nm:
                    name_map[cid] = nm
    return name_map

CARD_ID_RE = re.compile(r'^[A-Z][A-Z0-9_]+$')

def looks_like_id(s):
    return bool(CARD_ID_RE.match(s))

def fix_names(names, name_map):
    fixed = 0
    result = []
    for item in names:
        if isinstance(item, list):
            inner, cnt = fix_names(item, name_map)
            result.append(inner)
            fixed += cnt
        elif isinstance(item, str) and looks_like_id(item):
            mapped = name_map.get(item, item)
            if mapped != item:
                print(f"  {item} → {mapped}")
                fixed += 1
            result.append(mapped)
        else:
            result.append(item)
    return result, fixed

def main():
    name_map = load_name_map()
    print(f"Loaded {len(name_map)} card name mappings")

    comps_path = os.path.join(DATA_DIR, "bg_comps.json")
    with open(comps_path, encoding="utf-8") as f:
        comps = json.load(f)

    total_fixed = 0
    for comp in comps:
        comp_id = comp.get("id", "?")
        for field in ("core_names", "addon_names"):
            if field in comp:
                fixed_list, cnt = fix_names(comp[field], name_map)
                if cnt:
                    print(f"[{comp_id}] {field}: fixed {cnt} entries")
                    total_fixed += cnt
                comp[field] = fixed_list

    with open(comps_path, "w", encoding="utf-8") as f:
        json.dump(comps, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Fixed {total_fixed} entries in bg_comps.json")

if __name__ == "__main__":
    main()
