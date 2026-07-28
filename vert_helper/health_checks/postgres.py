from __future__ import annotations

from .types import HealthCheckResult

try:
    import psycopg2
    from psycopg2 import OperationalError
except ImportError:  # pragma: no cover
    psycopg2 = None
    OperationalError = Exception


def check_postgres(context: dict) -> HealthCheckResult:
    if psycopg2 is None:
        return HealthCheckResult(
            status="FAILED",
            message="Dependencia psycopg2 nao instalada",
        )

    host = context.get("host") or context.get("pg_host") or "localhost"
    port = int(context.get("port") or context.get("pg_port") or 5432)
    timeout = float(context.get("timeout") or 3)
    dbname = context.get("database") or context.get("pg_db")
    user = context.get("user") or context.get("pg_user")
    password = context.get("password") or context.get("pg_password")

    if not dbname:
        return HealthCheckResult(
            status="UNKNOWN",
            message="database/pg_db nao informado",
        )

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=int(timeout),
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        return HealthCheckResult(status="OK")
    except OperationalError as exc:
        return HealthCheckResult(status="FAILED", message=str(exc))
    except Exception as exc:
        return HealthCheckResult(status="FAILED", message=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
