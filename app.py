import os
import time
import hmac
import hashlib
import requests
from flask import Flask, request
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()
APIKEY = os.getenv("BINGX_APIKEY")
SECRETKEY = os.getenv("BINGX_SECRETKEY")

API_BASE = "https://open-api.bingx.com"

app = Flask(__name__)

# 注文設定（フラグごと）
ORDER_CONFIG = {
    "long_blue": {
        "side": "BUY",
        "position": "LONG",
        "quantity_usdt": 100,
        "leverage": 10,
        "margin_type": "SEPARATE_ISOLATED",
        "stop_loss_percent": -50,
        "trailing_take_profit_percent": 25,
        "trailing_width_percent": 5
    },
    "long_yang": {
        "side": "BUY",
        "position": "LONG",
        "quantity_usdt": 100,
        "leverage": 10,
        "margin_type": "SEPARATE_ISOLATED",
        "stop_loss_percent": -50,
        "trailing_take_profit_percent": 25,
        "trailing_width_percent": 5
    },
    "short_gold": {
        "side": "SELL",
        "position": "SHORT",
        "quantity_usdt": 100,
        "leverage": 10,
        "margin_type": "SEPARATE_ISOLATED",
        "stop_loss_percent": -50,
        "trailing_take_profit_percent": 35,
        "trailing_width_percent": 5
    },
    "short_in": {
        "side": "SELL",
        "position": "SHORT",
        "quantity_usdt": 100,
        "leverage": 10,
        "margin_type": "SEPARATE_ISOLATED",
        "stop_loss_percent": -50,
        "trailing_take_profit_percent": 35,
        "trailing_width_percent": 5
    }
}

# --------------------
# ヘルパー関数
# --------------------
def get_signature(params):
    sorted_params = "&".join(f"{k}={v}" for k,v in sorted(params.items()))
    return hmac.new(SECRETKEY.encode(), sorted_params.encode(), hashlib.sha256).hexdigest()

def send_request(path, method, params):
    params["timestamp"] = int(time.time() * 1000)
    signature = get_signature(params)
    url = f"{API_BASE}{path}?{'&'.join(f'{k}={v}' for k,v in params.items())}&signature={signature}"
    headers = {"X-BX-APIKEY": APIKEY}
    response = requests.request(method, url, headers=headers)
    return response.json()

def get_market_price(symbol):
    resp = requests.get(f"{API_BASE}/openApi/market/ticker/24hr?symbol={symbol}")
    price = float(resp.json().get('lastPrice', 0))
    return price

def usdt_to_quantity(symbol, usdt_amount):
    price = get_market_price(symbol)
    return round(usdt_amount / price, 6)  # 小数点6桁

# --------------------
# 注文関数（テスト注文＋実注文＋損切り＋トレーリング利確）
# --------------------
def send_order(flag):
    cfg = ORDER_CONFIG[flag]
    symbol = "BTC-USDT"
    quantity = usdt_to_quantity(symbol, cfg["quantity_usdt"])
    
    # 1. テスト注文（安全確認用）
    test_params = {
        "symbol": symbol,
        "side": cfg["side"],
        "positionSide": cfg["position"],
        "type": "MARKET",
        "quantity": quantity,
        "marginType": cfg["margin_type"],
        "leverage": cfg["leverage"]
    }
    resp_test = send_request("/openApi/swap/v2/trade/order/test", "POST", test_params)
    print("テスト注文:", resp_test)
    
    # 2. 実注文
    real_params = test_params.copy()
    resp_real = send_request("/openApi/swap/v2/trade/order", "POST", real_params)
    print("実注文:", resp_real)
    
    # 3. 損切り・トレーリング利確設定
    last_price = get_market_price(symbol)
    stop_price = round(last_price * (1 + cfg["stop_loss_percent"]/100), 2)
    take_price = round(last_price * (1 + cfg["trailing_take_profit_percent"]/100), 2)
    
    trailing_params = {
        "symbol": symbol,
        "side": cfg["side"],
        "positionSide": cfg["position"],
        "quantity": quantity,
        "stopPrice": stop_price,
        "takeProfitPrice": take_price,
        "trailingDelta": cfg["trailing_width_percent"],
        "type": "TRAILING_TAKE_PROFIT_MARKET"
    }
    
    resp_trail = send_request("/openApi/swap/v2/trade/order/stop", "POST", trailing_params)
    print("損切り＋トレーリング設定:", resp_trail)

# --------------------
# Webhook受信
# --------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    text = request.data.decode('utf-8')
    flag = None
    if "BTCUSDT 144m 青玉" in text:
        flag = "long_blue"
    elif "BTCUSDT 144m 陽線" in text:
        flag = "long_yang"
    elif "BTCUSDT 144m 金玉" in text:
        flag = "short_gold"
    elif "BTCUSDT 144m 陰線" in text:
        flag = "short_in"
    
    if flag:
        print(f"フラグ検出: {flag}, 通知内容: {text}")
        send_order(flag)
    else:
        print("該当フラグなし:", text)
    
    return "OK", 200

# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
