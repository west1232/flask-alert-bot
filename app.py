import os
import time
import hmac
from hashlib import sha256
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 環境変数からAPIキーを取得
APIKEY = os.getenv("APIKEY")
SECRETKEY = os.getenv("SECRETKEY")

APIURL = "https://open-api.bingx.com"

# フラグ判定用のルール
def get_flag(text):
    if "BTCUSDT 144m 青玉" in text:
        return 1  # ロング、TP+25%、SL-50%、トレール5%
    elif "BTCUSDT 144m 陽線" in text:
        return 2  # ロング、TP+25%、SL-50%、トレール5%
    elif "BTCUSDT 144m 金玉" in text:
        return 3  # ショート、TP+35%、SL-50%、トレール5%
    elif "BTCUSDT 144m 陰線" in text:
        return 4  # ショート、TP+35%、SL-50%、トレール5%
    else:
        return 0  # 何もしない

def get_sign(api_secret, payload):
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

def parse_params(params):
    sorted_keys = sorted(params)
    params_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
    return params_str + "&timestamp=" + str(int(time.time() * 1000))

def send_order(flag):
    # 注文パラメータ設定
    if flag == 1 or flag == 2:
        side = "BUY"
        take_profit_percent = 25
    elif flag == 3 or flag == 4:
        side = "SELL"
        take_profit_percent = 35
    else:
        return {"result": "No action"}

    sl_percent = -50
    trail_percent = 5
    leverage = 10
    usdt_amount = 100

    params = {
        "symbol": "BTC-USDT",
        "side": side,
        "positionSide": "LONG" if side=="BUY" else "SHORT",
        "type": "MARKET",
        "marginType": "SEPARATE_ISOLATED",
        "leverage": leverage,
        "quantity": usdt_amount,
        "takeProfit": f'{{"type": "TRAILING_STOP_MARKET","callbackRate": {trail_percent},"activationPrice": 0}}',
        "stopLoss": f'{{"stopPrice": 0,"type":"STOP_MARKET"}}'
    }

    params_str = parse_params(params)
    signature = get_sign(SECRETKEY, params_str)
    url = f"{APIURL}/openApi/swap/v2/trade/order/test?{params_str}&signature={signature}"
    headers = {"X-BX-APIKEY": APIKEY}
    response = requests.post(url, headers=headers)
    return response.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    text = request.data.decode("utf-8")
    flag = get_flag(text)
    result = send_order(flag)
    return jsonify({"flag": flag, "result": result, "status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
