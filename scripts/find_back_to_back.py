import json

data = json.load(open('data/bg_minions_cache.json', encoding='utf-8'))
keywords = ['背靠背', 'back to back', '巴林達', '巴琳達', '附魔師', 'balinda', 'enchant']
for m in data:
    name = m.get('name','')
    cid = m.get('id','')
    text = m.get('text','')
    for kw in keywords:
        if kw.lower() in name.lower() or kw.lower() in text.lower():
            tl = m.get('tech_level','?')
            races = m.get('races',[])
            print(f"{cid} | T{tl} | {name} | {races}")
            print(f"  text: {text[:100]}")
            break
