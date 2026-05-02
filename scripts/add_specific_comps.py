import json, os

# These are the two specific comps the user asked for
new_comps = [
  {
    "id": "dragon_ring_bearer",
    "tier": "S",
    "name": "戒指持有者全攻聖盾流",
    "races": ["NAGA", "DRAGON"],
    "difficulty": "hard",
    "core": ["BG34_921", "BG25_016", "BG29_813", "BG24_500"],
    "core_names": ["戒指持有者", "辛多雷直擊者", "堅持的吟詩龍", "琥珀守護者"],
    "addon": [
      ["BGS_119", "BG28_741", "BGS_071", "BG31_812"],
      ["BG23_009", "BG34_865", "BG26_175", "BG35_921"]
    ],
    "addon_names": [
      ["霹靂旋風", "充能女皇", "偏斜防護機器人", "保衛者艾克膿"],
      ["熔岩潛伏者", "烈焰巨靈", "驚喜元素", "深淵衛士"]
    ],
    "strategy": "核心機制：戒指持有者（NAGA/DRAGON）在每次友方手下攻擊時施放「刺眼戒指」，讓場上隨從持續獲得聖盾術保護。辛多雷直擊者天生聖盾術＋風怒，每回合攻擊兩次觸發兩次戒指效果。堅持的吟詩龍讓旁邊的龍族永久保留聖盾術及戰鬥體質。充能女皇在你施放旅店法術時為所有有聖盾術的隨從追加+3攻擊力，形成聖盾→充能→攻擊→新聖盾的完美循環。",
    "tips": [
      "戒指持有者需在中後期（T6）才能找到，前期優先拿聖盾術手下",
      "辛多雷直擊者一定要放在場上，風怒讓他每回合觸發兩次戒指",
      "充能女皇搭配旅店法術能讓聖盾手下攻擊力爆炸性成長",
      "堅持的吟詩龍要放在有高攻擊力龍族旁讓永久體質加持",
      "此流爆發力極高但需精確排板，練習各手下的位置配置"
    ]
  },
  {
    "id": "back_to_back_ballers",
    "tier": "A",
    "name": "背靠背T2球手連鎖爆發流",
    "races": ["ELEMENTAL"],
    "difficulty": "medium",
    "core": ["BG31_816", "BG31_818", "BG31_815", "BG31_810"],
    "core_names": ["火球手", "雪球手", "沙丘居怪", "紫外線晉升者"],
    "addon": [
      ["BG31_812", "BG26_175", "BG34_950", "BGS_119"],
      ["BGS_116", "BG34_865", "BG28_707", "BG34_858"]
    ],
    "addon_names": [
      ["保衛者艾克膿", "驚喜元素", "石器巨碑", "霹靂旋風"],
      ["重置異常體", "烈焰巨靈", "活化的艾澤萊晶岩", "陣風亡魄"]
    ],
    "strategy": "火球手（T2）出售時全體+1攻擊力並強化下一個球手；雪球手（T2）出售時全體+1生命值並強化下一個球手。關鍵在於「背靠背」：連續出售並重購球手，讓下一張球手越來越強，出售效果也越來越大，最終整個場面獲得大量累積加成。沙丘居怪開局在旅店放置增益，紫外線晉升者讓所有元素在戰鬥時額外獲得+3/+2（每次打出元素都會增強）。",
    "tips": [
      "核心玩法：每回合出售球手→從旅店買新球手→再次出售，每次全場+1攻或+1血",
      "火球手和雪球手可以穿插使用，攻擊力和生命值均衡成長效果最佳",
      "每賣出一張球手，下一張同名球手的效果就更強，盡早開始疊層",
      "沙丘居怪在開局就要放進去讓旅店元素都有基礎加成",
      "紫外線晉升者在打出多張元素後能給全體大量加成，後期轉成強力戰力"
    ]
  }
]

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bg_comps.json")
with open(DATA_PATH, encoding='utf-8') as f:
    existing = json.load(f)

existing_ids = {c['id'] for c in existing}
added = []
for comp in new_comps:
    if comp['id'] not in existing_ids:
        existing.append(comp)
        added.append(comp['name'])
    else:
        # Update existing
        for i, c in enumerate(existing):
            if c['id'] == comp['id']:
                existing[i] = comp
                added.append(f"[UPDATED] {comp['name']}")
                break

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"Total: {len(existing)} comps")
print(f"Added/Updated: {added}")
tiers = {"S":[], "A":[], "B":[], "C":[]}
for c in existing:
    tiers[c['tier']].append(c['name'])
for t, names in tiers.items():
    print(f"  Tier {t} ({len(names)}): {', '.join(names)}")
