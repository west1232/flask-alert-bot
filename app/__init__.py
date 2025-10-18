from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    # Render の環境変数 SECRET_KEY を使用
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
