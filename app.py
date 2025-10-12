from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Discord通知（MacroDroid経由）のテキストを受け取る
    text = request.data.decode('utf-8')  # プレーンテキストで受信
    print(f"通知受信: {text}")
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render が割り当てたポートを使用
    app.run(host='0.0.0.0', port=port)
