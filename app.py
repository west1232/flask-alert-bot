from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Discord通知（MacroDroid経由）のテキストを受け取る
    text = request.data.decode('utf-8')  # ← JSONではなくプレーンテキストで受信
    print(f"通知受信: {text}")
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
