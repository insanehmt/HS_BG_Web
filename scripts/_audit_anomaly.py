"""審核變異快取的問題：重複、遺失、過濾不當"""
import urllib.request, json, gzip, re

url = 'https://api.hearthstonejson.com/v1/latest/zhTW/cards.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try:
    raw = gzip.decompress(raw)
except Exception:
    pass
cards = json.loads(raw.decode('utf-8', 'ignore'))

anomalies = [c for c in cards if c.get('type') == 'BATTLEGROUND_ANOMALY' and c.get('name')]

print("=== 目前過濾器會保留的（非 t 結尾）===")
kept = []
filtered_out = []
for c in sorted(anomalies, key=lambda x: x.get('id','')):
    cid = c.get('id','')
    if re.search(r"t\d*$", cid):
        filtered_out.append(c)
    else:
        kept.append(c)

print(f"保留 {len(kept)} 張，過濾掉 {len(filtered_out)} 張")

# 找重複名稱
from collections import Counter
name_count = Counter(c.get('name','') for c in kept)
dupes = {n: cnt for n, cnt in name_count.items() if cnt > 1}
if dupes:
    print(f"\n重複名稱（{len(dupes)} 種）：")
    for name, cnt in sorted(dupes.items(), key=lambda x: -x[1]):
        ids = [c.get('id') for c in kept if c.get('name') == name]
        print(f"  [{cnt}x] {name} → {ids}")
else:
    print("無重複名稱")

print(f"\n=== 被過濾掉的（t 結尾）===")
for c in filtered_out:
    print(f"  {c.get('id',''):40s} | {c.get('name','')}")

print(f"\n=== 保留清單（ID + name）===")
for c in kept:
    print(f"  {c.get('id',''):40s} | {c.get('name','')}")
