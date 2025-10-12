from flask import Flask, request, jsonify
import requests
import time
import hmac
import hashlib
import os

app = Flask(__name__)

# === BingX 接続情報 ===
API_URL = "https://open-api.bingx.com"
APIKEY = os.getenv("APIKEY")
SECRETKEY = os.getenv("SECRETKEY")

# === 署名作成関数 ===
def get_sign(secret, query_string):
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

# === パラメータ整形 ===
def parse_params(params):
    params['timestamp'] = int(time.time() * 1000)
    return '&'.join([f"{k}={v}" for k, v in sorted(params.items())])

# === API送信関数（署名付き） ===
def send_signed_request(method, path, params):
    query_string = parse_params(params)
    signature = get_sign(SECRETKEY, query_string)
    url = f"{API_URL}{path}?{query_string}&signature={signature}"
    headers = {'X-BX-APIKEY': APIKEY}
    response = requests.request(method, url, headers=headers)
    try:
        return response.json()
    except Exception:
        return {"error": response.text}

# === メインWebhook ===
@app.route('/webhook', methods=['POST'])
def webhook():
    text = request.data.decode('utf-8')

    # フラグ識別
    flag = 0
    order_result = {}

    # === ① 青玉（ロング） ===
    if "BTCUSDT 144m 青玉" in text:
        flag = 1
        order_result = place_test_order(
            symbol="BTC-USDT",
            side="BUY",
            position_side="LONG",
            take_profit_trigger=25,
            trailing_callback=5,
            stop_loss_percent=-50
        )

    # === ② 陽線（ロング） ===
    elif "BTCUSDT 144m 陽線" in text:
        flag = 2
        order_result = place_test_order(
            symbol="BTC-USDT",
            side="BUY",
            position_side="LONG",
            take_profit_trigger=25,
            trailing_callback=5,
            stop_loss_percent=-50
        )

    # === ③ 金玉（ショート） ===
    elif "BTCUSDT 144m 金玉" in text:
        flag = 3
        order_result = place_test_order(
            symbol="BTC-USDT",
            side="SELL",
            position_side="SHORT",
            take_profit_trigger=35,
            trailing_callback=5,
            stop_loss_percent=-50
        )

    # === ④ 陰線（ショート） ===
    elif "BTCUSDT 144m 陰線" in text:
        flag = 4
        order_result = place_test_order(
            symbol="BTC-USDT",
            side="SELL",
            position_side="SHORT",
            take_profit_trigger=35,
            trailing_callback=5,
            stop_loss_percent=-50
        )

    else:
        order_result = {"message": "No matching flag found."}

    return jsonify({"flag": flag, "result": order_result, "status": "ok"})


# === 注文実行関数（テスト注文） ===
def place_test_order(symbol, side, position_side, take_profit_trigger, trailing_callback, stop_loss_percent):
    """
    実際の注文では /openApi/swap/v2/trade/order に変更。
    テスト注文は /openApi/swap/v2/trade/order/test を使用。
    """
    params = {
        "symbol": symbol,
        "side": side,                # BUY or SELL
        "positionSide": position_side,  # LONG or SHORT
        "type": "MARKET",            # 成行
        "quantity": 100,             # USDでの想定
        "reduceOnly": False,
        "takeProfit": f'{{"type":"TRAILING_STOP_MARKET","callbackRate":{trailing_callback},"activationPrice":0.0}}',
        "stopLoss": '{"stopPrice":0.0,"type":"STOP_MARKET"}'
    }

    # テスト注文API
    return send_signed_request("POST", "/openApi/swap/v2/trade/order/test", params)


# === Renderサーバー起動設定 ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

