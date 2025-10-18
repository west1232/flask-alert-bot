# app/__init__.py
from flask import Flask

app = Flask(__name__)
app.secret_key = "dev_secret_key"

@app.route("/")
def hello():
    return "Hello Flask App!"
