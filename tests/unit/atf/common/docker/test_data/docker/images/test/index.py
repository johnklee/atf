#!/usr/bin/env python3
import os
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/name")
def name():
    return "My name is John"

if __name__ == "__main__":
    app.run(host= '0.0.0.0')
