import sys
sys.path.insert(0, r'F:\\GitHub_Copilot\\HS_BattleGrounds')
from log_parser import PowerLogParser

log = r'D:\\BZGame\\Hearthstone\\Logs\\Hearthstone_2026_05_04_02_48_48\\Power.log'
try:
    with open(log, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()[-2000:]
    p = PowerLogParser(log, '', name_resolver=lambda cid: cid)
    games = p.parse_lines(lines)
    print('[test] Parsed {} new games'.format(len(games)))
except Exception as e:
    import traceback
    print('[test] Exception:', e)
    traceback.print_exc()
