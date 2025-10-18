from flask import Blueprint, request, render_template, redirect, url_for, session
import os, json

main_bp = Blueprint('main', __name__)

# /admin
@main_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    if request.method == 'POST':
        if 'password' in request.form:
            # ログイン処理
            if request.form.get('password') == ADMIN_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('main.admin'))
            else:
                return render_template('admin.html', error='パスワードが違います')
        else:
            # ルールON/OFF切替
            try:
                with open('config/rules.json', 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                symbol = request.form.get('symbol')
                timeframe = request.form.get('timeframe')
                if symbol in rules and timeframe in rules[symbol]:
                    rules[symbol][timeframe] = not rules[symbol][timeframe]
                with open('config/rules.json', 'w', encoding='utf-8') as f:
                    json.dump(rules, f, indent=2)
            except Exception as e:
                return f"Error: {e}"
            return redirect(url_for('main.admin'))

    # GET
    if session.get('logged_in'):
        try:
            with open('config/rules.json', 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except FileNotFoundError:
            rules = {}
        return render_template('admin.html', rules=rules)
    else:
        return render_template('admin.html')


# /webhook（Discord通知受信用骨格）
@main_bp.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received Discord webhook:", data)
    # TODO: ここで通知解析やルール判定を追加
    return "OK", 200
