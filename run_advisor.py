"""
爐石傳說標準對戰輔助工具 — 啟動腳本
放在 HS_BattleGrounds 根目錄，直接執行即可

執行：
    python run_advisor.py
    python run_advisor.py "C:/Users/你的使用者名稱/AppData/Local/Blizzard/Hearthstone/Logs/Power.log"
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hs_advisor"))
from hs_advisor import monitor, DEFAULT_LOG

log_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG
monitor(log_path)
