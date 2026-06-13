"""找出 BG 變異牌（Anomaly）的資料結構"""
import urllib.request, json, gzip

url = 'https://api.hearthstonejson.com/v1/latest/zhTW/cards.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
try:
    raw = gzip.decompress(raw)
except Exception:
    pass
cards = json.loads(raw.decode('utf-8', 'ignore'))

print("=== BATTLEGROUND_ANOMALY 類型 ===")
anomalies = [c for c in cards if c.get('type') == 'BATTLEGROUND_ANOMALY' and c.get('name')]
for c in sorted(anomalies, key=lambda x: x.get('id','')):
    print(f"  {c.get('id',''):40s} | {c.get('name',''):30s} | set={c.get('set')} | pool={c.get('isBattlegroundsPoolMinion')} | timewarp={c.get('battlegroundsTimewarpCard')}")

print(f"\n共 {len(anomalies)} 張")

print("\n=== 含 ANOMALY mechanic 的 BG 牌 ===")
for c in cards:
    cid = c.get('id','')
    if not cid.startswith('BG'):
        continue
    mechs = c.get('mechanics', [])
    if 'ANOMALY' in mechs or 'BATTLEGROUND_ANOMALY' in mechs:
        print(f"  {cid:40s} | {c.get('name',''):30s} | type={c.get('type')} | mechs={mechs}")

print("\n=== 有 battlegroundsAnomalyCard 或類似欄位 ===")
for c in cards:
    cid = c.get('id','')
    if not cid.startswith('BG'):
        continue
    for k, v in c.items():
        if 'anomal' in k.lower() or 'Anomal' in k:
            print(f"  {cid} | {k}={v} | name={c.get('name','')}")
            break
