import os
import socket

from flask import Flask
from flask import render_template

app = Flask(__name__, static_folder="static")


@app.route("/")
def send_file():
    hostname = socket.gethostname()
    return render_template("index.html", hostname=hostname)


@app.route("/healthz")
def healthz():
    return "up"


app.run(use_reloader=False, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0")
