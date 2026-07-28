from __future__ import annotations

from .types import HealthCheckResult


def check_s3(context: dict) -> HealthCheckResult:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        return HealthCheckResult(
            status="FAILED",
            message="Dependencia boto3 nao instalada",
        )

    try:
        context_boto3 = {
            "region_name": context.get("region_name", None),
            "aws_access_key_id": context.get("aws_access_key_id", None),
            "aws_secret_access_key": context.get("aws_secret_access_key", None),
            "endpoint_url": context.get("endpoint_url", None),
        }
        boto3.client(
            "s3",
            **context_boto3,
        )
        return HealthCheckResult(status="OK")
    except (BotoCoreError, ClientError) as exc:
        return HealthCheckResult(status="FAILED", message=str(exc))
