from flask import Flask, jsonify, request
import os
import requests
import dns.resolver

from telemetry import configure_comprehend_telemetry


app = Flask(__name__)
configure_comprehend_telemetry("petstore-api", app=app)


# Catalog service (currently works)
CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "http://catalog-service:5000"
)


def resolve_service(service_name):
    """
    Resolve ECS Cloud Map SRV service.
    Example:
    orders-service.petstore.local
    ->
    http://172.31.22.225:32769
    """

    try:
        answers = dns.resolver.resolve(
            service_name,
            "SRV"
        )

        record = answers[0]

        host = str(record.target).rstrip(".")
        port = record.port

        return f"http://{host}:{port}"

    except Exception as e:
        raise Exception(
            f"Service discovery failed for {service_name}: {e}"
        )


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
        response = requests.get(
            f"{CATALOG_URL}/products",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/orders", methods=["GET"])
def get_orders():

    try:
        orders_url = resolve_service(
            "orders-service.petstore.local"
        )

        response = requests.get(
            f"{orders_url}/orders",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/orders", methods=["POST"])
def create_order():

    try:
        orders_url = resolve_service(
            "orders-service.petstore.local"
        )

        response = requests.post(
            f"{orders_url}/orders",
            json=request.get_json(),
            headers={
                "Content-Type": "application/json"
            },
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001
    )