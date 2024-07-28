import os
from flask import Flask, flash, render_template, redirect, request
import bot

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret")

app.register_blueprint(bot.bot_bp)


@app.route("/")
def main():
    return "Hello, World!"


if __name__ == "__main__":
    app.run()
