import json

with open(r'F:\GitHub_Copilot\HS_BattleGrounds\data\bg_minions_cache.json', encoding='utf-8') as f:
    m = json.load(f)

def find(keywords):
    results = []
    for c in m:
        name = c['name']
        text = c.get('text', '')
        races = ','.join(c.get('races') or [])
        for k in keywords:
            if k in name or k in text:
                results.append(f"{c['id']:22s} T{c.get('tech_level','?')} {races:20s} {name} | {text[:80].replace(chr(10),' ')}")
                break
    return results

# 1. Back to Back - what is it?
print("=== Back to Back candidates ===")
for r in find(['背靠背','相同','之後的','接連','連鎖','buff','chain']):
    print(r)

print("\n=== Smuggler / 走私 Quilboar ===")
for r in find(['走私','賞金','偷帶','購買','野豬','鮮血寶石']):
    print(r)

print("\n=== Bounty Pirates ===")
for r in find(['賞金','海盜','黃金','報賞']):
    print(r)

print("\n=== Beast Banana 香蕉 ===")
for r in find(['香蕉','果實','水果','野獸','自傷','對自己','banana']):
    print(r)

print("\n=== Kalecgos Dragons 卡雷苟斯 ===")
for r in find(['卡雷苟斯','法術傷害','龍族法術','施法']):
    print(r)

print("\n=== Avenge Quilboar 復仇 ===")
for r in find(['復仇','報復','手下死亡','友方死亡','野豬']):
    print(r)

print("\n=== Automaton Mechs 自動機 ===")
for r in find(['自動機','遠古自動機','組裝','合體','機械']):
    print(r[:5] for r in find(['遠古','自動機']))
    break

print("\n=== Deep Blue Nagas 深藍 ===")
for r in find(['深藍','深淵','深海','納迦','法術','疊加']):
    print(r)

print("\n=== Scam Murlocs 詐騙 ===")
for r in find(['詐騙','騙術','魚人','急速','快攻','偷竊']):
    print(r)

print("\n=== Self Damage Beasts 自傷 ===")
for r in find(['自傷','對你的英雄造成','對自己','造成傷害','野獸']):
    print(r)

print("\n=== Stegodon Beasts 劍齒 ===")
for r in find(['劍齒','劍龍','板背','硬甲','重甲']):
    print(r)

print("\n=== Mrrglton Murlocs 魚人鎮 ===")
for r in find(['魚人鎮','mrrglton','賣店','合唱','叫囂']):
    print(r)

print("\n=== Handbuff Murlocs 手牌增益 ===")
for r in find(['手中','手牌','手裡','手上有','在手中']):
    print(r)

print("\n=== End of Turn Undead 回合結束亡靈 ===")
for r in find(['回合結束','你的回合結束','每當你的回合','亡靈']):
    print(r)

print("\n=== Overflow Undead 溢出 ===")
for r in find(['溢出','過量','溢位','超過','額外亡語','大量']):
    print(r)

print("\n=== Elemental Shop Buff 元素旅店 ===")
for r in find(['旅店','增益','賦予旅店','旅店中的','元素']):
    print(r)
