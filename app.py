from flask import Flask, request, jsonify
import time, hmac, requests, os, json
from hashlib import sha256

# ======================
# 初期設定
# ======================
APIURL = "https://open-api.bingx.com"
APIKEY = os.environ.get("APIKEY")
SECRETKEY = os.environ.get("SECRETKEY")
USE_REAL_ORDERS = os.environ.get("USE_REAL_ORDERS", "false").lower() == "true"
USDT_AMOUNT = float(os.environ.get("USDT_AMOUNT", 100))
LEVERAGE = int(os.environ.get("LEVERAGE", 10))

app = Flask(__name__)

# ======================
# 汎用関数
# ======================
def get_sign(api_secret, payload):
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join([f"{x}={paramsMap[x]}" for x in sortedKeys])
    return paramsStr + "&timestamp=" + str(int(time.time() * 1000))

def send_request(method, path, paramsMap, retry=3):
    paramsStr = parseParam(paramsMap)
    signature = get_sign(SECRETKEY, paramsStr)
    url = f"{APIURL}{path}?{paramsStr}&signature={signature}"
    headers = {'X-BX-APIKEY': APIKEY}
    
    for i in range(retry):
        try:
            response = requests.request(method, url, headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            app.logger.warning(f"API request failed ({i+1}/{retry}): {e}")
            time.sleep(1)
    return {"error": "API request failed after retries"}

def get_current_price(symbol="BTC-USDT"):
    try:
        url = f"{APIURL}/openApi/swap/v2/quote/price?symbol={symbol}"
        res = requests.get(url, timeout=5)
        return float(res.json()["data"]["price"])
    except Exception as e:
        app.logger.error(f"価格取得失敗: {e}")
        return None

# ======================
# 発注関数（クロス、SL/TP/トレーリング反映）
# ======================
def place_order(symbol, side, positionSide):
    current_price = get_current_price(symbol)
    if not current_price:
        return {"error": "価格取得に失敗しました"}

    # 数量をUSDT換算で計算
    qty = round(USDT_AMOUNT * LEVERAGE / current_price, 4)

    # ----------------------
    # TP/SL/トレーリング（レバレッジ除外1/10で計算）
    # ----------------------
    if side == "BUY":  # ロング
        sl_price = round(current_price * 0.95, 2)       # ▲50% → 1/10
        tp_price = round(current_price * 1.025, 2)      # +25% → 1/10
        trailing_pct = 0.5
    else:  # SELL / ショート
        sl_price = round(current_price * 1.05, 2)       # +50% → 1/10
        tp_price = round(current_price * 0.965, 2)      # −35% → 1/10
        trailing_pct = 0.5

    stop_loss = json.dumps({"type": "STOP_MARKET", "stopPrice": sl_price})
    take_profit = json.dumps({"type": "TRAILING_STOP_MARKET", "activationPrice": tp_price, "callbackRate": trailing_pct})

    path = "/openApi/swap/v2/trade/order" if USE_REAL_ORDERS else "/openApi/swap/v2/trade/order/test"

    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": positionSide,
        "type": "MARKET",
        "quantity": qty,
        "marginType": "CROSSED",
        "leverage": LEVERAGE,
        "takeProfit": take_profit,
        "stopLoss": stop_loss,
    }

    result = send_request("POST", path, params)
    return {
        "mode": "REAL" if USE_REAL_ORDERS else "TEST",
        "entry_price": current_price,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "params": params,
        "api_result": result
    }

# ======================
# Webhook
# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    text = request.data.decode("utf-8").strip()
    app.logger.info(f"通知受信: {text}")

    flag = 0
    order_info = {}

    if "BTCUSDT 144m" in text:
        if "青玉" in text or "陽線" in text:
            flag = 1 if "青玉" in text else 2
            order_info = place_order("BTC-USDT", "BUY", "LONG")
        elif "金玉" in text or "陰線" in text:
            flag = 3 if "金玉" in text else 4
            order_info = place_order("BTC-USDT", "SELL", "SHORT")

    return jsonify({"status": "ok", "flag": flag, "order_info": order_info})

# ======================
# メイン
# ======================
if __name__ == "__main__":
    app.logger.setLevel("INFO")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
