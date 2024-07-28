import os
from flask import Flask, flash, render_template, redirect, request
from tasks import add
import bot

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret")

app.register_blueprint(bot.bot_bp)


@app.route("/")
def main():
    return "Hello, World!"


@app.route("/add", methods=["POST"])
def add_inputs():
    x = int(request.form["x"] or 0)
    y = int(request.form["y"] or 0)
    add.delay(x, y)
    flash("Your addition job has been submitted.")
    return redirect("/")


if __name__ == "__main__":
    app.run()
