"""
push_to_web.py — 推送本地資料到雲端網站

用法:
    python scripts/push_to_web.py               # 推送 API（快速，Render 重啟後消失）
    python scripts/push_to_web.py --commit       # 推送 + git commit（永久，觸發重新部署）
    python scripts/push_to_web.py --all          # 包含大型卡牌快取
    python scripts/push_to_web.py --url https://your-app.onrender.com --token xxx

也可設環境變數 或 建立 .push_config:
    WEB_URL=https://your-app.onrender.com
    SYNC_TOKEN=your_secret_token
"""
import os, sys, json, argparse, requests
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 預設同步（頻繁更動）
DEFAULT_FILES = [
    "bg_comps.json",
    "hero_meta.json",
    "hsreplay_meta_cache.json",
    "bg_config.json",
]

# --all 時額外同步（大型卡牌快取，換版本才需要更新）
ALL_FILES = DEFAULT_FILES + [
    "bg_minions_cache.json",
    "bg_spells_cache.json",
    "bg_trinkets_cache.json",
    "bg_heroes_cache.json",
]


def main():
    parser = argparse.ArgumentParser(description="推送本地資料到雲端")
    parser.add_argument("--url",   default=os.environ.get("WEB_URL", ""),
                        help="雲端網址，例如 https://your-app.onrender.com")
    parser.add_argument("--token", default=os.environ.get("SYNC_TOKEN", ""),
                        help="SYNC_TOKEN（需與雲端環境變數一致）")
    parser.add_argument("--all",   action="store_true",
                        help="同步所有資料（含大型卡牌快取）")
    parser.add_argument("--commit", action="store_true",
                        help="同步後執行 git add + commit + push（資料永久保存，觸發 Render 重新部署）")
    args = parser.parse_args()

    # --- 設定檔讀取（若有 .push_config 則自動帶入）---
    config_path = Path(__file__).parent.parent / ".push_config"
    if config_path.exists():
        for line in config_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("WEB_URL=") and not args.url:
                args.url = line[len("WEB_URL="):]
            elif line.startswith("SYNC_TOKEN=") and not args.token:
                args.token = line[len("SYNC_TOKEN="):]

    if not args.url:
        print("❌ 請提供雲端網址：")
        print("   python scripts/push_to_web.py --url https://... --token ...")
        print("   或建立 .push_config 檔案，內含：")
        print("   WEB_URL=https://...")
        print("   SYNC_TOKEN=your_secret")
        sys.exit(1)

    if not args.token:
        print("❌ 請提供 SYNC_TOKEN（須與雲端 SYNC_TOKEN 環境變數一致）")
        sys.exit(1)

    files_to_sync = ALL_FILES if args.all else DEFAULT_FILES

    # --- 讀取檔案 ---
    payload = {}
    for fname in files_to_sync:
        fpath = DATA_DIR / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                payload[fname] = json.load(f)
            size_kb = fpath.stat().st_size // 1024
            print(f"  ✓ {fname} ({size_kb} KB)")
        else:
            print(f"  ⚠️  略過 {fname}（不存在）")

    if not payload:
        print("❌ 沒有可同步的資料")
        sys.exit(1)

    # --- 推送 ---
    url = args.url.rstrip("/") + "/api/push-data"
    print(f"\n📤 推送到 {url} ...")
    try:
        r = requests.post(url, json={"token": args.token, "files": payload}, timeout=60)
    except requests.exceptions.ConnectionError:
        print("❌ 無法連線，請確認網址是否正確")
        sys.exit(1)

    if r.status_code == 200:
        result = r.json()
        print(f"\n✅ 成功更新 {result.get('updated', 0)} 個檔案：")
        for f in result.get("files", []):
            print(f"   • {f}")
        if result.get("skipped"):
            print(f"⚠️  略過（不在白名單）：{result['skipped']}")

        # --commit：git add + commit + push → Render 自動重新部署
        if args.commit:
            print("\n📦 git commit 中（讓資料永久保存）...")
            import subprocess
            root = str(Path(__file__).parent.parent)
            data_files = [str(DATA_DIR / f) for f in payload.keys()]
            subprocess.run(["git", "add"] + data_files, cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "data: 更新爬蟲資料"], cwd=root, check=True)
            subprocess.run(["git", "push"], cwd=root, check=True)
            print("✅ git push 完成，Render 將在 3-5 分鐘內自動重新部署")
    elif r.status_code == 403:
        print("❌ Token 錯誤，請確認 SYNC_TOKEN 設定")
        sys.exit(1)
    elif r.status_code == 503:
        print("❌ 雲端未設定 SYNC_TOKEN 環境變數")
        sys.exit(1)
    else:
        print(f"❌ 失敗：HTTP {r.status_code}")
        print(r.text[:500])
        sys.exit(1)


if __name__ == "__main__":
    main()
