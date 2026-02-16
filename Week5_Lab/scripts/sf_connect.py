import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")

    required = [
        "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER",
        "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"
    ]

    # Auth-specific required fields
    if not authenticator:
        required.append("SNOWFLAKE_PASSWORD")
    elif authenticator.lower() in {"oauth", "programmatic_access_token", "pat_with_external_session"}:
        required.append("SNOWFLAKE_TOKEN")

    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}. Fill .env from .env.example")

    conn_kwargs = dict(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        token=os.getenv("SNOWFLAKE_TOKEN"),
        role=os.getenv("SNOWFLAKE_ROLE", None),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

    # Optional external browser auth / oauth token auth
    if authenticator:
        conn_kwargs["authenticator"] = authenticator
        auth_lower = authenticator.lower()
        if auth_lower in {"oauth", "programmatic_access_token", "pat_with_external_session"}:
            conn_kwargs.pop("password", None)
        elif auth_lower == "externalbrowser":
            conn_kwargs.pop("password", None)
            conn_kwargs.pop("token", None)

    return snowflake.connector.connect(**{k: v for k, v in conn_kwargs.items() if v})
