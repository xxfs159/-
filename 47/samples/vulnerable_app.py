from flask import Flask, request
import hashlib
import pickle
import subprocess


app = Flask(__name__)
api_key = "prod-7aA9superSecretToken"


@app.route("/user")
def user():
    user_id = request.args.get("id")
    sql = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(sql)
    return "ok"


@app.route("/run")
def run():
    cmd = request.args.get("cmd")
    return subprocess.check_output(cmd, shell=True)


def load_payload(raw):
    return pickle.loads(raw)


def digest(value):
    return hashlib.md5(value).hexdigest()


app.run(debug=True)
