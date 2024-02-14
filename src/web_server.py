import os
import threading

from flask import Flask
from flask import send_from_directory

app = Flask(__name__, static_folder="static")
port = int(os.environ.get("PORT", 8080))


@app.route("/")
def send_file():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/healthz")
def healthz():
    return "up"


app.run(use_reloader=False, port=port, host="0.0.0.0")
