import os
import time
import hmac
from hashlib import sha256
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

APIURL = "https://testnet.bingx.com"
APIKEY = os.getenv("BINGX_APIKEY")
SECRETKEY = os.getenv("BINGX_SECRETKEY")

app = Flask(__name__)

# --- 補助関数 ---
def get_sign(secret, payload):
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

def get_symbol_price(symbol="BTC-USDT"):
    """現在価格を取得"""
    path = f"/openApi/swap/v2/market/ticker/price?symbol={symbol}"
    resp = requests.get(APIURL + path)
    data = resp.json()
    return float(data.get("price", 0))

def send_order(symbol, side, usdt_amount, leverage, stop_loss_pct, trail_take_pct, trail_pct):
    """テストネット用の成行注文発注"""
    current_price = get_symbol_price(symbol)
    quantity = round(usdt_amount / current_price, 6)  # BTC数量に換算

    # 損切・トレーリング価格計算
    if side == "BUY":
        stop_price = round(current_price * (1 - stop_loss_pct/100), 2)
        activate_price = round(current_price * (1 + trail_take_pct/100), 2)
    else:
        stop_price = round(current_price * (1 + stop_loss_pct/100), 2)
        activate_price = round(current_price * (1 - trail_take_pct/100), 2)
    
    path = "/openApi/swap/v2/trade/order/test"
    method = "POST"
    
    paramsMap = {
        "symbol": symbol,
        "side": side,
        "positionSide": "LONG" if side=="BUY" else "SHORT",
        "type": "MARKET",
        "quantity": quantity,
        "leverage": leverage,
        "marginType": "ISOLATED",
        "stopLoss": {
            "type": "STOP_MARKET",
            "stopPrice": stop_price,
            "workingType": "MARK_PRICE"
        },
        "trailingTakeProfit": {
            "activatePrice": activate_price,
            "callbackRate": trail_pct,
            "workingType": "MARK_PRICE"
        }
    }
    
    timestamp = int(time.time() * 1000)
    paramsStr = "&".join([f"{k}={paramsMap[k]}" for k in paramsMap])
    paramsStr += f"&timestamp={timestamp}"
    signature = get_sign(SECRETKEY, paramsStr)
    
    url = f"{APIURL}{path}?{paramsStr}&signature={signature}"
    headers = {"X-BX-APIKEY": APIKEY}
    resp = requests.post(url, headers=headers, json={})
    return resp.json()

# --- Webhook & 判定 ---
@app.route("/webhook", methods=["POST"])
def webhook():
    text = request.data.decode("utf-8")
    print(f"通知受信: {text}")
    
    order_params = []

    # フラグ判定
    if "BTCUSDT 144m" in text and "青玉" in text:
        order_params.append({"side":"BUY","stop_loss":50,"trail_tp":25,"trail_width":5})
    elif "BTCUSDT 144m" in text and "陽線" in text:
        order_params.append({"side":"BUY","stop_loss":50,"trail_tp":25,"trail_width":5})
    elif "BTCUSDT 144m" in text and "金玉" in text:
        order_params.append({"side":"SELL","stop_loss":50,"trail_tp":35,"trail_width":5})
    elif "BTCUSDT 144m" in text and "陰線" in text:
        order_params.append({"side":"SELL","stop_loss":50,"trail_tp":35,"trail_width":5})
    
    results = []
    for op in order_params:
        res = send_order(
            symbol="BTC-USDT",
            side=op["side"],
            usdt_amount=100,
            leverage=10,
            stop_loss_pct=op["stop_loss"],
            trail_take_pct=op["trail_tp"],
            trail_pct=op["trail_width"]
        )
        results.append(res)
    
    return jsonify({"status":"ok","orders":results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
