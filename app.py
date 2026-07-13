from flask import Flask, jsonify, request
import os
import requests
from telemetry import configure_comprehend_telemetry

app = Flask(__name__)
configure_comprehend_telemetry("petstore-api", app=app)

# Cloud Map service discovery
CATALOG_URL = os.getenv("CATALOG_URL", "http://catalog-service:5000")
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:5000")


@app.route("/")
def home():
    return "PetStore API Gateway running with OpenTelemetry!"


@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        response = requests.get(f"{CATALOG_URL}/products", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/orders", methods=["GET"])
def get_orders():
    try:
        response = requests.get(f"{ORDERS_URL}/orders", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/orders", methods=["POST"])
def create_order():
    try:
        response = requests.post(
            f"{ORDERS_URL}/orders",
            json=request.get_json(),
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)