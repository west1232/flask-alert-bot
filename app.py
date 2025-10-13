from flask import Flask, request, jsonify
import os

# 🔹 Flask インスタンスは必ずグローバルに
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    # POST データ取得
    if request.data:
        text = request.data.decode("utf-8").strip()
    elif request.form:
        text = next(iter(request.form.values()))
    else:
        text = ""

    # ログ出力
    app.logger.info(f"通知受信: {text}")

    # レスポンスを返すだけ
    return jsonify({"status": "ok", "received_text": text})

# Render の場合 gunicorn で起動するため main 内での Flask インスタンス作成は不要
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.setLevel("INFO")
    app.run(host="0.0.0.0", port=port)
