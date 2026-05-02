"""
scrape_firestone_comps.py
從 Firestone 爬取最新牌組數據，合併至 bg_comps.json
用法: python scripts/scrape_firestone_comps.py
"""
import json, os, sys, gzip, re

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
COMPS_PATH   = os.path.join(DATA_DIR, 'bg_comps.json')
MINIONS_PATH = os.path.join(DATA_DIR, 'bg_minions_cache.json')

# 族群中文名
TRIBE_ZH = {
    'BEAST': '野獸', 'MURLOC': '魚人', 'MECHANICAL': '機械',
    'DEMON': '惡魔', 'DRAGON': '龍族', 'PIRATE': '海盜',
    'QUILBOAR': '野豬人', 'ELEMENTAL': '元素', 'NAGA': '納迦',
    'UNDEAD': '亡靈', 'ALL': '全族', 'NONE': '中立',
}

# compId → 中文名（固定映射）
NAME_ZH = {
    'beast_self_damage':    '自傷野獸流',
    'beast_stegodon':       '劍龍野獸流',
    'demon_fodder':         '食料惡魔流',
    'dragon_kalecgos':      '卡雷苟斯龍族流',
    'elemental_tier2_ballers': '二費球手元素流',
    'quilboar_avenge':      '復仇野豬人流',
    'quilboar_smuggler':    '走私野豬人流',
    'mech_automaton':       '自動機機械流',
    'mech_shield':          '護盾機械流',
    'murloc_mrrglton':      '魚人鎮流',
    'murloc_handbuff':      '手牌強化魚人流',
    'murloc_scam':          '詐騙魚人流',
    'naga_spellspam':       '法術狂納迦流',
    'naga_deep_blue':       '深藍納迦流',
    'pirate_bounty':        '賞金海盜流',
    'undead_attack':        '進攻亡靈流',
    'undead_end_of_turn':   '回合結束亡靈流',
    'undead_overflow':      '溢出亡靈流',
    'neutral_back_to_back': '連續觸發流',
    'beast_banana':         '香蕉野獸流',
    'dragon_ring_bearer':   '戒指持有者龍族流',
    'elemental_shop_buff':  '旅店強化元素流',
}

# compId → races 映射（Firestone forcedTribes 通常是空的）
RACES_MAP = {
    'beast_self_damage':    ['BEAST'],
    'beast_stegodon':       ['BEAST'],
    'demon_fodder':         ['DEMON'],
    'dragon_kalecgos':      ['DRAGON'],
    'elemental_tier2_ballers': ['ELEMENTAL'],
    'quilboar_avenge':      ['QUILBOAR'],
    'quilboar_smuggler':    ['QUILBOAR'],
    'mech_automaton':       ['MECHANICAL'],
    'mech_shield':          ['MECHANICAL'],
    'murloc_mrrglton':      ['MURLOC'],
    'murloc_handbuff':      ['MURLOC'],
    'murloc_scam':          ['MURLOC'],
    'naga_spellspam':       ['NAGA'],
    'naga_deep_blue':       ['NAGA'],
    'pirate_bounty':        ['PIRATE'],
    'undead_attack':        ['UNDEAD'],
    'undead_end_of_turn':   ['UNDEAD'],
    'undead_overflow':      ['UNDEAD'],
    'neutral_back_to_back': [],
    'beast_banana':         ['BEAST'],
    'dragon_ring_bearer':   ['DRAGON', 'NAGA'],
    'elemental_shop_buff':  ['ELEMENTAL'],
}


def fetch_firestone_data():
    """使用 Playwright 抓取 Firestone 牌組策略與統計數據。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("需要安裝 playwright：pip install playwright && playwright install chromium")

    strategies = None
    stats_map = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        captured = {}

        def on_response(resp):
            url = resp.url
            if 'bgs-comps-strategies' in url or 'comp-stats' in url:
                try:
                    body = resp.body()
                    try:
                        body = gzip.decompress(body)
                    except Exception:
                        pass
                    captured[url] = json.loads(body.decode('utf-8', 'ignore'))
                    print(f'  ✓ 已抓取: {url[:80]} ({len(body)} bytes)')
                except Exception as e:
                    print(f'  ✗ 讀取失敗: {url[:60]} {e}')

        page.on('response', on_response)
        print('正在載入 Firestone...')
        page.goto('https://www.firestoneapp.com/battlegrounds/comps',
                  wait_until='networkidle', timeout=40000)

        for url, data in captured.items():
            if 'strategies' in url:
                strategies = data
            elif 'comp-stats' in url:
                for s in data.get('compStats', []):
                    arch = s.get('archetype', '')
                    stats_map[arch] = {
                        'avg_placement': round(s.get('averagePlacement', 0), 2),
                        'data_points':   s.get('dataPoints', 0),
                    }

        browser.close()

    if not strategies:
        raise RuntimeError('無法取得牌組策略數據')

    return strategies, stats_map


def build_name_map():
    """從 bg_minions_cache.json 建立 card_id → 中文名 映射。"""
    name_map = {}
    if not os.path.exists(MINIONS_PATH):
        return name_map
    with open(MINIONS_PATH, encoding='utf-8') as f:
        minions = json.load(f)
    for m in minions:
        cid = m.get('id') or m.get('card_id', '')
        name = m.get('name', '')
        if cid and name:
            name_map[cid] = name
    return name_map


def parse_comp(comp_data, stats_map, name_map, existing_map):
    """將一條 Firestone 牌組數據轉換為我們的格式。"""
    cid = comp_data['compId']
    original_name = comp_data.get('name', cid)
    power_level = comp_data.get('powerLevel', 'C')
    difficulty = comp_data.get('difficulty', 'Medium').lower()
    cards = comp_data.get('cards', [])

    # 區分 CORE / ADDON / CYCLE
    core_ids = [c['cardId'] for c in cards if c.get('status') == 'CORE']
    addon_ids = [c['cardId'] for c in cards
                 if c.get('status') in ('ADDON', 'CYCLE')]

    # 英文 tips 轉換（如果沒有中文版）
    en_tips = []
    for t in comp_data.get('tips', []):
        if t.get('language') == 'enUS' and t.get('tip'):
            en_tips.append(t['tip'])

    # 查中文名
    def zh_name(card_id):
        return name_map.get(card_id, card_id)

    core_names = [zh_name(cid) for cid in core_ids]
    addon_names = [zh_name(cid) for cid in addon_ids]

    # 統計數據
    stat = stats_map.get(cid, {})

    # 保留已有的中文 strategy / tips
    existing = existing_map.get(cid, {})
    strategy = existing.get('strategy', '')
    tips_zh = existing.get('tips', [])

    # 若沒有中文 strategy，用英文 tips 拼湊
    if not strategy and en_tips:
        strategy = ' '.join(en_tips[:2])

    return {
        'id':            cid,
        'tier':          power_level,
        'name':          NAME_ZH.get(cid, existing.get('name', original_name)),
        'original_name': original_name,
        'races':         RACES_MAP.get(cid, existing.get('races', [])),
        'difficulty':    difficulty,
        'core':          core_ids,
        'core_names':    core_names,
        'addon':         [addon_ids] if addon_ids else [],
        'addon_names':   [addon_names] if addon_names else [],
        'strategy':      strategy,
        'tips':          tips_zh,
        'avg_placement': stat.get('avg_placement'),
        'data_points':   stat.get('data_points', 0),
        'patch':         comp_data.get('patchNumber'),
    }


def scrape_and_save():
    """主流程：抓取 → 解析 → 合併 → 儲存。"""
    print('=== Firestone 牌組爬蟲 ===')

    # 讀取現有牌組（保留中文策略）
    existing_map = {}
    if os.path.exists(COMPS_PATH):
        with open(COMPS_PATH, encoding='utf-8') as f:
            existing = json.load(f)
        for c in existing:
            existing_map[c['id']] = c
        print(f'現有牌組: {len(existing_map)} 筆')

    # 建立卡片中文名映射
    name_map = build_name_map()
    print(f'卡片名稱映射: {len(name_map)} 筆')

    # 抓取 Firestone 數據
    strategies, stats_map = fetch_firestone_data()
    print(f'Firestone 牌組: {len([c for c in strategies if c.get("compId") and c.get("cards")])} 筆')
    print(f'統計數據: {len(stats_map)} 筆')

    # 解析並合併
    FIRESTONE_ID_ALIASES = {
        "demon_fodder": "fodder_demons", "quilboar_smuggler": "smuggler_quilboar",
        "pirate_bounty": "bounty_pirates", "neutral_back_to_back": "back_to_back",
        "dragon_kalecgos": "kalecgos_dragons", "quilboar_avenge": "avenge_quilboar",
        "mech_automaton": "automaton_mechs", "mech_shield": "shield_mechs",
        "murloc_scam": "scam_murlocs", "naga_spellspam": "spellspam_nagas",
        "naga_deep_blue": "deep_blue_nagas", "undead_attack": "attack_undead",
        "beast_self_damage": "self_damage_beasts", "beast_stegodon": "stegodon_beasts",
        "elemental_tier2_ballers": "tier2_ballers", "murloc_mrrglton": "mrrglton_murlocs",
        "murloc_handbuff": "handbuff_murlocs", "undead_end_of_turn": "end_of_turn_undead",
        "undead_overflow": "overflow_undead",
    }

    # ID → existing（含 alias）
    id_to_existing = dict(existing_map)
    for new_id, old_id in FIRESTONE_ID_ALIASES.items():
        if old_id in existing_map:
            id_to_existing[new_id] = existing_map[old_id]

    comps = []
    updated_ids = set()
    for comp_data in strategies:
        if not comp_data.get('compId') or not comp_data.get('cards'):
            continue
        comp = parse_comp(comp_data, stats_map, name_map, id_to_existing)
        # 補中文 strategy/tips（如果已有）
        ec = id_to_existing.get(comp['id'])
        if ec:
            if not comp['strategy'] and ec.get('strategy'):
                comp['strategy'] = ec['strategy']
            if not comp['tips'] and ec.get('tips'):
                comp['tips'] = ec['tips']
        comps.append(comp)
        updated_ids.add(comp['id'])
        if comp['id'] in FIRESTONE_ID_ALIASES:
            updated_ids.add(FIRESTONE_ID_ALIASES[comp['id']])

    # 保留自訂牌組
    custom = [ec for eid, ec in existing_map.items() if eid not in updated_ids]
    all_comps = comps + custom

    # 依 tier 排序
    tier_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4}
    all_comps.sort(key=lambda c: (tier_order.get(c['tier'], 9), c['name']))

    # 儲存
    with open(COMPS_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_comps, f, ensure_ascii=False, indent=2)

    print(f'\n✓ 已儲存 {len(all_comps)} 筆牌組（Firestone {len(comps)} + 自訂 {len(custom)}）至 {COMPS_PATH}')
    print()

    # 統計
    from collections import Counter
    tier_counts = Counter(c['tier'] for c in all_comps)
    for tier in ['S', 'A', 'B', 'C', 'D']:
        if tier in tier_counts:
            names = [c['name'] for c in all_comps if c['tier'] == tier]
            print(f'  {tier} ({tier_counts[tier]}): {", ".join(names)}')

    return all_comps


if __name__ == '__main__':
    scrape_and_save()
