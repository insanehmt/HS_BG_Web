import json, os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bg_comps.json")
with open(DATA_PATH, encoding='utf-8') as f:
    comps = json.load(f)

for c in comps:
    if c['id'] == 'back_to_back':
        # Correct core cards per user:
        # 1. Back to Back (BG35_952) - Tavern Spell T4: Give a minion +4/+4, future casts give extra +4/+4
        # 2. 巴琳達‧石爐 (BG35_883) - T6: Your targeted spells cast twice
        # 3. 德拉克瑞附魔師 (BG26_ICC_901) - T5: Your end-of-turn effects trigger twice
        # 4. 骷髏懲擊者 (BG35_334) - T5 UNDEAD: End-of-turn +1/+1 to all your minions
        c['core'] = ["BG35_952", "BG35_883", "BG26_ICC_901", "BG35_334"]
        c['core_names'] = ["背靠背", "巴琳達‧石爐", "德拉克瑞附魔師", "骷髏懲擊者"]
        c['strategy'] = (
            "核心法術「背靠背」每次施放給目標隨從+4/+4，且之後每次施放額外+4/+4，愈疊愈強。"
            "巴琳達‧石爐讓你對友方隨從的法術施放兩次，使每次背靠背直接翻倍效果。"
            "德拉克瑞附魔師讓回合結束效果觸發兩次，搭配骷髏懲擊者的回合結束全體+1/+1實現雪球式成長。"
            "目標是把背靠背集中打在一隻核心隨從上，快速打出超高數值的主力。"
        )
        c['tips'] = [
            "巴琳達讓背靠背法術施放兩次 → 第一次已是+8/+8，之後每次再翻倍累積",
            "德拉克瑞附魔師讓骷髏懲擊者回合結束全體+2/+2，快速帶動整個板面",
            "選定一隻速攻或風怒隨從作為背靠背的集中目標，確保能打出傷害",
            "背靠背是T4法術，前期先穩住板面，4費解鎖後立刻開始疊加",
            "搭配有額外效果的高體質隨從當目標，例如嘲諷或連擊效果"
        ]
        print(f"Updated: {c['name']}")
        print(f"  core: {c['core']}")
        print(f"  core_names: {c['core_names']}")
        break

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(comps, f, ensure_ascii=False, indent=2)

print("Done.")
