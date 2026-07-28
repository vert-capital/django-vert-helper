from __future__ import annotations

from .types import HealthCheckResult

try:
    from confluent_kafka.admin import AdminClient
except ImportError:  # pragma: no cover
    AdminClient = None


def check_kafka(context: dict) -> HealthCheckResult:
    if AdminClient is None:
        return HealthCheckResult(
            status="FAILED",
            message="Dependencia confluent-kafka nao instalada",
        )

    servers = context.get("bootstrap_servers") or context.get("brokers") or []
    timeout = float(context.get("timeout") or 3)

    if isinstance(servers, str):
        servers = [servers]

    if not servers:
        return HealthCheckResult(
            status="UNKNOWN",
            message="bootstrap_servers nao informado",
        )

    client_config = {
        "bootstrap.servers": ",".join(str(s) for s in servers),
        "socket.timeout.ms": int(timeout * 1000),
    }

    security_mapping = {
        "security_protocol": "security.protocol",
        "sasl_mechanism": "sasl.mechanism",
        "sasl_username": "sasl.username",
        "sasl_password": "sasl.password",
        "ssl_ca_location": "ssl.ca.location",
        "ssl_certificate_location": "ssl.certificate.location",
        "ssl_key_location": "ssl.key.location",
        "ssl_key_password": "ssl.key.password",
    }
    for source_key, target_key in security_mapping.items():
        value = context.get(source_key)
        if value:
            client_config[target_key] = value

    try:
        admin = AdminClient(client_config)
        admin.list_topics(timeout=timeout)
        return HealthCheckResult(status="OK")
    except Exception as exc:
        return HealthCheckResult(status="FAILED", message=str(exc))
