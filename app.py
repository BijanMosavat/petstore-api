from flask import Flask, Blueprint, jsonify
import os
import requests
from telemetry import configure_comprehend_telemetry

app = Flask(__name__)
configure_comprehend_telemetry("petstore-api", app=app)

api = Blueprint("api", __name__, url_prefix="/api")

CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:5000")

@app.route("/")
def home():
    return "Petshop running with OpenTelemetry active!"

@app.route("/health")
@app.route("/api/health")
def health():
    return {"status": "ok"}

@app.route("/catalog")
@app.route("/api/catalog")
def catalog():
    response = requests.get(f"{CATALOG_URL}/products", timeout=5)
    return jsonify(response.json())

app.register_blueprint(api)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)