"""
本機執行：偵測 Firestone 實際使用的 API 端點。
用法：python scripts/detect_firestone_api.py
需要：pip install playwright && playwright install chromium
"""
import json, gzip, sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("請先安裝：pip install playwright && playwright install chromium")
    sys.exit(1)

TARGET = "https://www.firestoneapp.com/battlegrounds/comps"
print(f"開啟 {TARGET} …\n")

captured = []   # (url, content_type, size, preview)

def on_response(resp):
    url = resp.url
    ct  = resp.headers.get("content-type", "")
    # 略過圖片/字型/css/js chunk
    low = url.lower()
    if any(low.endswith(x) for x in (".png",".jpg",".webp",".svg",".woff",".woff2",".ttf",".ico")):
        return
    if "chunk" in low and low.endswith(".js"):
        return
    try:
        body = resp.body()
        if not body:
            return
        # 嘗試解壓
        try:
            body = gzip.decompress(body)
        except Exception:
            pass
        size = len(body)
        if size < 20:
            return
        # 嘗試解析 JSON
        try:
            data = json.loads(body.decode("utf-8", "ignore"))
            preview = json.dumps(data, ensure_ascii=False)[:120]
            captured.append((url, "json", size, preview))
        except Exception:
            # 非 JSON，記錄 content-type 和大小
            if "json" in ct or size > 500:
                preview = body[:80].decode("utf-8", "ignore").replace("\n", " ")
                captured.append((url, ct[:30], size, preview))
    except Exception:
        pass

import time

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)   # headless=False 看得到畫面
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )
    page = ctx.new_page()
    page.on("response", on_response)

    try:
        page.goto(TARGET, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"[goto 超時或錯誤，繼續等待] {e}")

    print("等待頁面完整載入（10 秒）…")
    time.sleep(10)
    browser.close()

print(f"\n共攔截到 {len(captured)} 個回應\n")
print("=" * 80)

# 找可能含策略資料的 JSON（有 compId / cards / strategies 關鍵字）
candidates = []
others = []
for url, ct, size, preview in captured:
    if ct == "json" and any(k in preview for k in ("compId","cards","strategies","archetype","powerLevel")):
        candidates.append((url, size, preview))
    else:
        others.append((url, ct, size, preview))

if candidates:
    print("★ 可能含策略資料的端點：")
    for url, size, preview in candidates:
        print(f"  URL  : {url}")
        print(f"  大小 : {size} bytes")
        print(f"  預覽 : {preview}")
        print()
else:
    print("★ 未找到含策略資料的端點（請把下方 '其他 JSON' 回報給開發者）\n")

print("-" * 80)
print("其他 JSON / 資料回應（按大小排序）：")
for url, ct, size, preview in sorted(others, key=lambda x: -x[2])[:30]:
    print(f"  [{ct:20s}] {size:6d}b  {url}")
    print(f"             預覽: {preview}")
    print()
