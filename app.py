from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    text = data.get("text", "")
    print("通知受信:", text)

    if "BUY_SIGNAL" in text:
        print("🚀 BUY_SIGNAL 検知！自動売買を実行！")
        # ここに取引所API呼び出しを後で追加予定

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
