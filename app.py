import requests

WEBHOOK_URL = "https://your-app.onrender.com/webhook"
TEST_MESSAGES = [
    "BTCUSDT 144m 青玉",
    "BTCUSDT 144m 陽線",
    "BTCUSDT 144m 金玉",
    "BTCUSDT 144m 陰線"
]

for msg in TEST_MESSAGES:
    try:
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(WEBHOOK_URL, data=msg.encode("utf-8"), headers=headers, timeout=15)
        data = response.json()
    except Exception as e:
        print(f"送信: {msg}")
        print(f"レスポンス取得に失敗: {e}")
        print("-" * 40)
        continue

    print(f"送信: {msg}")
    print(f"レスポンス: {data}")
    print("-" * 60)
