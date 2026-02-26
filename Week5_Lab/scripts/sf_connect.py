import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    token = os.getenv("SNOWFLAKE_TOKEN")
    password = os.getenv("SNOWFLAKE_PASSWORD")

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")

    conn_kwargs = dict(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        role=os.getenv("SNOWFLAKE_ROLE", None),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

    if authenticator and authenticator.lower() in {"programmatic_access_token", "oauth", "pat_with_external_session"}:
        conn_kwargs["authenticator"] = authenticator
        conn_kwargs["token"] = token
    elif authenticator and authenticator.lower() == "externalbrowser":
        conn_kwargs["authenticator"] = authenticator
    else:
        conn_kwargs["password"] = password

    return snowflake.connector.connect(**{k: v for k, v in conn_kwargs.items() if v})
