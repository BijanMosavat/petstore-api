from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "http://catalog-service:5000"
)

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/catalog")
def catalog():
    response = requests.get(
        f"{CATALOG_URL}/products",
        timeout=5
    )
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001
    )