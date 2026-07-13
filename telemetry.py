import os
import uuid

DEFAULT_COMPREHEND_TOKEN = "comprehend_HU94rP7Rd2z1oFxfu_TTLIebc_87D9dc0yPkXDSU9T_fpcUd"


def configure_comprehend_telemetry(service_name: str, app=None):
    token = os.getenv("COMPREHEND_SDK_TOKEN") or DEFAULT_COMPREHEND_TOKEN
    os.environ["COMPREHEND_SDK_TOKEN"] = token

    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError as e:
        print(f"Telemetry Warning: Missing OpenTelemetry dependencies. {e}")
        return None

    try:
        from comprehend_telemetry import ComprehendDevSpanProcessor
    except ImportError:
        try:
            from comprehend_telemetry.span_processor import ComprehendDevSpanProcessor
        except ImportError as e:
            print(f"Telemetry Warning: Unable to load comprehend_telemetry SDK. {e}")
            return None

    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "production",
        "deployment.environment": os.getenv("OTEL_ENVIRONMENT", "prod"),
        "service.instance.id": str(uuid.uuid4()),
    })

    try:
        comprehend = ComprehendDevSpanProcessor(
            organization="bijan-sandbox",
            token=token,
            debug=True,
        )
    except TypeError:
        comprehend = ComprehendDevSpanProcessor(
            organization="bijan-sandbox",
            token=token,
        )

    span_processor = comprehend.get_span_processor() if hasattr(comprehend, "get_span_processor") else comprehend

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_processor)

    current_tracer_provider = trace.get_tracer_provider()
    if current_tracer_provider.__class__.__name__ == "ProxyTracerProvider":
        trace.set_tracer_provider(tracer_provider)
        active_tracer_provider = trace.get_tracer_provider()
    else:
        active_tracer_provider = current_tracer_provider
        if hasattr(active_tracer_provider, "add_span_processor"):
            active_tracer_provider.add_span_processor(span_processor)

    if hasattr(comprehend, "get_metrics_exporter"):
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(
                    comprehend.get_metrics_exporter(),
                    export_interval_millis=15000,
                )
            ],
        )
        metrics.set_meter_provider(meter_provider)
    else:
        print("Telemetry Info: Metrics exporter is unavailable in the installed SDK; tracing is enabled.")

    if app is not None:
        FlaskInstrumentor().instrument_app(app)

    RequestsInstrumentor().instrument()

    return active_tracer_provider