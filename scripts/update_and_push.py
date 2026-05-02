"""
update_and_push.py — 一鍵更新：本地爬蟲 + 推送到雲端

用法:
    python scripts/update_and_push.py           # 只更新組合（bg_comps.json）
    python scripts/update_and_push.py --all     # 更新組合 + 推送所有資料

也可單獨推送（不爬蟲）:
    python scripts/update_and_push.py --push-only
"""
import os, sys, argparse, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"

def run(script, *args):
    cmd = [sys.executable, str(SCRIPTS / script)] + list(args)
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode == 0

def scrape_via_api():
    """透過本地 Flask API 執行爬蟲。"""
    import requests
    base = "http://127.0.0.1:5000"
    print("\n═══ 執行 Firestone 爬蟲 ═══")
    try:
        r = requests.post(f"{base}/api/scrape-comps", timeout=120)
        d = r.json()
        if d.get("success"):
            print(f"  ✅ Firestone：updated={d.get('updated')} added={d.get('added')} total={d.get('total')}")
        else:
            print(f"  ❌ Firestone 失敗：{d.get('error')}")
    except Exception as e:
        print(f"  ❌ 無法連線 Flask（請先啟動本地伺服器）：{e}")
        return False

    print("\n═══ 執行 HSReplay 爬蟲 ═══")
    try:
        r = requests.post(f"{base}/api/scrape-hsreplay", timeout=120)
        d = r.json()
        if d.get("success"):
            print(f"  ✅ HSReplay：updated={d.get('updated')} added={d.get('added')}")
        else:
            print(f"  ❌ HSReplay 失敗：{d.get('error')}")
    except Exception as e:
        print(f"  ❌ HSReplay 失敗：{e}")

    return True

def main():
    parser = argparse.ArgumentParser(description="爬蟲更新 + 推送到雲端")
    parser.add_argument("--push-only", action="store_true", help="跳過爬蟲，只推送")
    parser.add_argument("--scrape-only", action="store_true", help="只爬蟲，不推送")
    parser.add_argument("--all", action="store_true", help="推送所有資料（含大型快取）")
    args = parser.parse_args()

    # 爬蟲
    if not args.push_only:
        ok = scrape_via_api()
        if not ok and not args.scrape_only:
            print("\n⚠️  爬蟲失敗，仍繼續推送現有資料...")

    # 推送
    if not args.scrape_only:
        print("\n═══ 推送到雲端 ═══")
        push_args = ["--all"] if args.all else []
        ok = run("push_to_web.py", *push_args)
        if ok:
            print("\n🎉 完成！雲端資料已更新。")
        else:
            print("\n❌ 推送失敗，請檢查 .push_config 設定")
            sys.exit(1)

if __name__ == "__main__":
    main()
