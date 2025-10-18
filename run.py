from app import create_app

# Flask アプリ生成
app = create_app()

if __name__ == "__main__":
    # 開発用サーバー起動（Render 上では gunicorn が使用）
    app.run(host="0.0.0.0", port=5000, debug=True)
