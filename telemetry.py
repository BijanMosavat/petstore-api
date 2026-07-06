import os
import uuid

def configure_comprehend_telemetry(service_name: str, app=None):
    token = os.getenv("COMPREHEND_SDK_TOKEN")
    if not token:
        print("Telemetry Warning: COMPREHEND_SDK_TOKEN environment variable not found.")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        
        # Instrumentation libraries
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        
        # Comprehend core SDK wrapper
        from comprehend_telemetry import ComprehendSDK
    except ImportError as e:
        print(f"Telemetry Warning: Missing OpenTelemetry dependencies. {e}")
        return None

    # 1. Create a descriptive resource identifier
    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "production",
        "deployment.environment": os.getenv("OTEL_ENVIRONMENT", "prod"),
        "service.instance.id": str(uuid.uuid4()),
    })

    # 2. Instantiate unified Comprehend SDK Client engine
    comprehend = ComprehendSDK(
        organization="bijan-sandbox",
        token=token,
        debug=False,
    )

    # 3. Configure Tracing
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(comprehend.get_span_processor())

    current_tracer_provider = trace.get_tracer_provider()
    if current_tracer_provider.__class__.__name__ == "ProxyTracerProvider":
        trace.set_tracer_provider(tracer_provider)
        active_tracer_provider = trace.get_tracer_provider()
    else:
        active_tracer_provider = current_tracer_provider
        if hasattr(active_tracer_provider, "add_span_processor"):
            active_tracer_provider.add_span_processor(comprehend.get_span_processor())

    # 4. Configure Metrics Engine (Required for live latency & mapping charts)
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                comprehend.get_metrics_exporter(),
                export_interval_millis=15000,
            )
        ],
    )
    trace.set_meter_provider(meter_provider)

    # 5. Initialize the Auto-Instrumentors
    if app is not None:
        FlaskInstrumentor().instrument_app(app)

    RequestsInstrumentor().instrument()

    return active_tracer_provider