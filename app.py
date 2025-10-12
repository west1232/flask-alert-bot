from flask import Flask, request, jsonify
import time, hmac, requests, os
from hashlib import sha256
from dotenv import load_dotenv

# ======================
# 初期設定
# ======================
load_dotenv()
APIURL = "https://open-api.bingx.com"
APIKEY = os.getenv("APIKEY")
SECRETKEY = os.getenv("SECRETKEY")

app = Flask(__name__)

# ======================
# 汎用関数
# ======================
def get_sign(api_secret, payload):
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    return paramsStr + "&timestamp=" + str(int(time.time() * 1000))

def send_request(method, path, paramsMap):
    paramsStr = parseParam(paramsMap)
    signature = get_sign(SECRETKEY, paramsStr)
    url = f"{APIURL}{path}?{paramsStr}&signature={signature}"
    headers = {'X-BX-APIKEY': APIKEY}
    response = requests.request(method, url, headers=headers)
    return response.json()

def get_current_price(symbol="BTC-USDT"):
    """BingXから現在価格を取得"""
    try:
        url = f"{APIURL}/openApi/swap/v2/quote/price?symbol={symbol}"
        res = requests.get(url)
        return float(res.json()["data"]["price"])
    except Exception as e:
        print("価格取得失敗:", e)
        return None

# ======================
# 注文関数
# ======================
def place_order(symbol, side, positionSide, marginType="ISOLATED", leverage=10, usdt_amount=100,
                stop_loss_pct=-50, tp_trigger_pct=25, trail_pct=5, test_mode=True):
    
    current_price = get_current_price(symbol)
    if not current_price:
        return {"error": "価格取得に失敗しました"}

    # 数量（USDT換算 → 枚数）
    qty = round(usdt_amount * leverage / current_price, 4)

    # 利確・損切価格を計算
    tp_price = round(current_price * (1 + tp_trigger_pct / 100), 2) if side == "BUY" else round(current_price * (1 - tp_trigger_pct / 100), 2)
    sl_price = round(current_price * (1 + stop_loss_pct / 100), 2) if side == "SELL" else round(current_price * (1 - stop_loss_pct / 100), 2)

    take_profit = {"type": "TRAILING_STOP_MARKET", "activationPrice": tp_price, "callbackRate": trail_pct}
    stop_loss = {"type": "STOP_MARKET", "stopPrice": sl_price}

    path = "/openApi/swap/v2/trade/order/test" if test_mode else "/openApi/swap/v2/trade/order"

    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": positionSide,
        "type": "MARKET",
        "quantity": qty,
        "marginType": marginType,
        "leverage": leverage,
        "takeProfit": str(take_profit).replace("'", '"'),
        "stopLoss": str(stop_loss).replace("'", '"'),
    }

    result = send_request("POST", path, params)
    return {"params": params, "api_result": result}

# ======================
# Webhook処理
# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    text = request.data.decode("utf-8").strip()
    print("通知受信:", text)

    flag = 0
    order_info = {}

    # --- フラグ判定 ---
    if "BTCUSDT 144m" in text and "青玉" in text:
        flag = 1
        order_info = place_order("BTC-USDT", "BUY", "LONG", tp_trigger_pct=25, stop_loss_pct=-50)
    elif "BTCUSDT 144m" in text and "陽線" in text:
        flag = 2
        order_info = place_order("BTC-USDT", "BUY", "LONG", tp_trigger_pct=25, stop_loss_pct=-50)
    elif "BTCUSDT 144m" in text and "金玉" in text:
        flag = 3
        order_info = place_order("BTC-USDT", "SELL", "SHORT", tp_trigger_pct=35, stop_loss_pct=-50)
    elif "BTCUSDT 144m" in text and "陰線" in text:
        flag = 4
        order_info = place_order("BTC-USDT", "SELL", "SHORT", tp_trigger_pct=35, stop_loss_pct=-50)

    return jsonify({"status": "ok", "flag": flag, "order_info": order_info})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
