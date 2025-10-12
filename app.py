from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    text = request.data.decode('utf-8')
    flags = {
        "flag1": "BTCUSDT 144m" in text and "青玉" in text,
        "flag2": "BTCUSDT 144m" in text and "陽線" in text,
        "flag3": "BTCUSDT 144m" in text and "金玉" in text,
        "flag4": "BTCUSDT 144m" in text and "陰線" in text,
    }

    print(f"通知受信: {text}")
    print(f"立ったフラグ: {flags}")

    # ここでフラグに応じて注文処理を呼び出せる
    # 例: if flags["flag1"]: place_order(...)

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
