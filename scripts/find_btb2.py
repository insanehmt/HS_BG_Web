import json

data = json.load(open('data/bg_minions_cache.json', encoding='utf-8'))
# Search for the actual "Back to Back" card - might be elemental/any race
# Also look for cards that strengthen next card or chain effects
for m in data:
    name = m.get('name','')
    cid = m.get('id','')
    text = m.get('text','')
    combined = (name + text).lower()
    if ('下一個' in combined and ('强化' in combined or '強化' in combined or '加強' in combined)) or \
       '連續' in combined or '背靠背' in combined or 'back' in combined.lower():
        tl = m.get('tech_level','?')
        races = m.get('races',[])
        print(f"{cid} | T{tl} | {name} | {races}")
        print(f"  text: {text[:120]}")
