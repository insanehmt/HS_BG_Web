"""
Auto-generate Chinese strategy + tips for comps that have English or empty content.
Usage: set GROQ_API_KEY=gsk_... && python generate_comp_descriptions.py
"""
import json, os, re, time
from groq import Groq

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COMPS_PATH = os.path.join(DATA_DIR, "bg_comps.json")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def is_chinese(s):
    if not s or not s.strip():
        return False
    return bool(re.search(r"[一-鿿]", s))


def needs_update(comp):
    strat = comp.get("strategy", "")
    tips = comp.get("tips", [])
    bad_tips = [t for t in tips if not is_chinese(t)]
    return not is_chinese(strat) or bad_tips or not tips


def generate_for_comp(comp):
    name = comp.get("name", comp["id"])
    core = comp.get("core_names", [])
    addon = comp.get("addon_names", [])
    if isinstance(addon[0], list) if addon else False:
        addon = [item for sub in addon for item in sub]
    tier = comp.get("tier", "")
    difficulty = comp.get("difficulty", "")
    races = comp.get("races", [])

    prompt = f"""你是爐石戰棋（Hearthstone Battlegrounds）的中文攻略作者。
請根據以下牌組資訊，用繁體中文生成：
1. strategy：一段2-4句的流派說明，描述核心機制和打法思路（不要列點）
2. tips：4-5條具體的操作提示（每條一句話）

牌組名稱：{name}
Tier：{tier} | 難度：{difficulty} | 族群：{', '.join(races) if races else '全族群'}
核心卡牌：{', '.join(core)}
備選卡牌：{', '.join(addon) if addon else '無'}

請以 JSON 格式回覆，格式如下：
{{
  "strategy": "...",
  "tips": ["...", "...", "...", "..."]
}}

只回覆 JSON，不要有其他文字。"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()
    # Extract JSON from response
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError(f"No JSON in response: {text}")
    return json.loads(match.group())


def main():
    with open(COMPS_PATH, encoding="utf-8") as f:
        comps = json.load(f)

    to_update = [(i, c) for i, c in enumerate(comps) if needs_update(c)]
    print(f"Found {len(to_update)} comps needing update")

    for idx, (i, comp) in enumerate(to_update):
        cid = comp["id"]
        print(f"[{idx+1}/{len(to_update)}] Generating: {cid}...", end=" ", flush=True)
        try:
            result = generate_for_comp(comp)
            comps[i]["strategy"] = result["strategy"]
            comps[i]["tips"] = result["tips"]
            print(f"OK - strategy: {result['strategy'][:40]}...")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.3)

    with open(COMPS_PATH, "w", encoding="utf-8") as f:
        json.dump(comps, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Updated {len(to_update)} comps in bg_comps.json")


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: Set GROQ_API_KEY environment variable first")
        print("  PowerShell: $env:GROQ_API_KEY = 'gsk_...'")
        exit(1)
    main()
