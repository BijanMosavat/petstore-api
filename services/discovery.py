import dns.resolver


def resolve_service(service_name):
    answers = dns.resolver.resolve(
        service_name,
        "SRV"
    )

    record = answers[0]

    host = str(record.target).rstrip(".")
    port = record.port

    return f"http://{host}:{port}"