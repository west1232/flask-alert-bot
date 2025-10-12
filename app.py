# app.py
from flask import Flask, request, jsonify
import os
import time
import requests
import hmac
from hashlib import sha256

app = Flask(__name__)

# Render 上で設定した環境変数から取得
APIKEY = os.environ.get("APIKEY")
SECRETKEY = os.environ.get("SECRETKEY")
APIURL = "https://open-api.bingx.com"

# フラグ判定関数
def get_flag(text):
    text = text.upper()
    if "BTCUSDT 144M 青玉" in text:
        return 1
    elif "BTCUSDT 144M 陽線" in text:
        return 2
    elif "BTCUSDT 144M 金玉" in text:
        return 3
    elif "BTCUSDT 144M 陰線" in text:
        return 4
    else:
        return 0  # 該当なし

# シグネチャ作成
def get_sign(secret, payload):
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

# パラメータを文字列化
def parse_params(params):
    sorted_keys = sorted(params)
    params_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
    if params_str != "":
        params_str += f"&timestamp={int(time.time() * 1000)}"
    else:
        params_str = f"timestamp={int(time.time() * 1000)}"
    return params_str

# APIリクエスト
def send_request(method, path, params_map):
    params_str = parse_params(params_map)
    signature = get_sign(SECRETKEY, params_str)
    url = f"{APIURL}{path}?{params_str}&signature={signature}"
    headers = {
        "X-BX-APIKEY": APIKEY,
        "Content-Type": "application/json"
    }
    response = requests.request(method, url, headers=headers)
    return response.text

# 注文作成（テストネット）
def place_order(flag):
    # デフォルトパラメータ
    symbol = "BTC-USDT"
    leverage = 10
    margin_type = "SEPARATE_ISOLATED"
    amount_usdt = 100
    side = "BUY"  # ロング
    position_side = "LONG"
    take_profit_price = None
    stop_loss_price = None
    trailing_percent = None

    # フラグごとの設定
    if flag == 1:  # ロング 青玉
        side = "BUY"
        position_side = "LONG"
        stop_loss_price = -50  # %損切り
        take_profit_price = 25  # %トレーリング利確発動
        trailing_percent = 5
    elif flag == 2:  # ロング 陽線
        side = "BUY"
        position_side = "LONG"
        stop_loss_price = -50
        take_profit_price = 25
        trailing_percent = 5
    elif flag == 3:  # ショート 金玉
        side = "SELL"
        position_side = "SHORT"
        stop_loss_price = -50
        take_profit_price = 35
        trailing_percent = 5
    elif flag == 4:  # ショート 陰線
        side = "SELL"
        position_side = "SHORT"
        stop_loss_price = -50
        take_profit_price = 35
        trailing_percent = 5
    else:
        return "No action"

    # 注文パラメータ
    params_map = {
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "type": "MARKET",
        "quantity": amount_usdt,
        "leverage": leverage,
        "marginType": margin_type,
        # 以下は実装例として JSON 文字列で渡す（BingX の形式に合わせて調整）
        "takeProfit": f'{{"type":"TAKE_PROFIT_MARKET","stopPrice":{take_profit_price},"price":{take_profit_price},"workingType":"MARK_PRICE"}}',
        "stopLoss": f'{{"type":"STOP_MARKET","stopPrice":{stop_loss_price},"workingType":"MARK_PRICE"}}',
        "trailingStop": f'{{"activationPrice":{take_profit_price},"callbackRate":{trailing_percent}}}'
    }

    return send_request("POST", "/openApi/swap/v2/trade/order/test", params_map)

# Webhook 受信
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        text = request.data.decode("utf-8")
        flag = get_flag(text)
        result = place_order(flag)
        print(f"通知受信: {text}, フラグ: {flag}, 注文結果: {result}")
        return jsonify({"status": "ok", "flag": flag, "result": result})
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
