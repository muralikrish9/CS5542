"""Drop and reload tables with new synthetic data."""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from sf_connect import get_conn

def run(cur, sql):
    cur.execute(sql)
    try: return cur.fetchall()
    except: return None

def main():
    with get_conn() as conn:
        cur = conn.cursor()

        # Recreate tables with AGENT_TYPE column
        print("Recreating tables...")
        run(cur, """
        CREATE OR REPLACE TABLE CS5542_WEEK5.PUBLIC.EVENTS (
            EVENT_ID STRING,
            EVENT_TIME TIMESTAMP_NTZ,
            TEAM STRING,
            CATEGORY STRING,
            VALUE FLOAT,
            AGENT_TYPE STRING
        );
        """)
        run(cur, """
        CREATE OR REPLACE TABLE CS5542_WEEK5.PUBLIC.USERS (
            USER_ID STRING,
            TEAM STRING,
            ROLE STRING,
            CREATED_AT TIMESTAMP_NTZ,
            AGENT_TYPE STRING
        );
        """)

        # Create stage + format
        run(cur, """
        CREATE OR REPLACE FILE FORMAT CS5542_CSV_FMT
            TYPE = CSV SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('', 'NULL', 'null');
        """)
        run(cur, "CREATE OR REPLACE STAGE CS5542_STAGE FILE_FORMAT = CS5542_CSV_FMT;")

        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

        for csv_file, table in [("events.csv", "EVENTS"), ("users.csv", "USERS")]:
            path = os.path.abspath(os.path.join(data_dir, csv_file))
            print(f"Uploading {csv_file}...")
            cur.execute(f"PUT file://{path} @CS5542_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;")
            print(f"  PUT: {cur.fetchall()}")

            t0 = time.time()
            cur.execute(f"""
            COPY INTO {table}
            FROM @CS5542_STAGE/{csv_file}.gz
            ON_ERROR='CONTINUE';
            """)
            res = cur.fetchall()
            dt = int((time.time() - t0) * 1000)
            print(f"  COPY: {res} ({dt}ms)")

        # Verify
        cur.execute("SELECT COUNT(*) FROM EVENTS")
        print(f"\nEvents loaded: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM USERS")
        print(f"Users loaded: {cur.fetchone()[0]}")
        cur.execute("SELECT AGENT_TYPE, COUNT(*) FROM EVENTS GROUP BY AGENT_TYPE ORDER BY 2 DESC")
        print("Events by agent type:", cur.fetchall())

        cur.close()

if __name__ == "__main__":
    main()
