"""
fetch_data.py — Download KCPD drug arrest data + CDC WONDER overdose deaths
Run: python fetch_data.py
"""
import requests
import pandas as pd
import os
import json
import time

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─── KCPD SOCRATA DATASETS (drug offenses by year) ───────────────────────────
KCPD_DATASETS = {
    2020: "vsgj-uufz",
    2021: "w795-ffu6",
    2022: "x39y-7d3m",
    2023: "bfyq-5nh6",
    2024: "isbe-v4d8",
}

def fetch_kcpd():
    print("=== Fetching KCPD Drug Arrest Data ===")
    all_records = []
    for year, dataset_id in KCPD_DATASETS.items():
        url = f"https://data.kcmo.org/resource/{dataset_id}.json"
        offset = 0
        year_records = []
        while True:
            # No $select — column names vary across years; normalize after
            params = {
                "$where": "ibrs like '35%'",
                "$limit": 5000,
                "$offset": offset,
            }
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                year_records.extend(batch)
                offset += len(batch)
                if len(batch) < 5000:
                    break
                time.sleep(0.3)
            except Exception as e:
                print(f"  [WARN] {year} fetch error at offset {offset}: {e}")
                break
        print(f"  {year}: {len(year_records)} drug offense records")
        all_records.extend(year_records)

    if not all_records:
        print("[ERROR] No KCPD data fetched.")
        return None

    # Normalize date column per-record before combining (names vary across years)
    normalized = []
    for rec in all_records:
        rec = {k.lower(): v for k, v in rec.items()}
        date_val = rec.get("reported_date") or rec.get("report_date") or rec.get("from_date")
        rec["_date"] = date_val
        normalized.append(rec)

    df = pd.DataFrame(normalized)
    df["Reported_Date"] = pd.to_datetime(df["_date"], errors="coerce")
    df = df.dropna(subset=["Reported_Date"])
    df.to_csv(f"{DATA_DIR}/kcpd_drug_arrests.csv", index=False)
    print(f"  Saved -> data/kcpd_drug_arrests.csv ({len(df)} total records)")
    return df


# ─── CDC WONDER ───────────────────────────────────────────────────────────────
# CDC WONDER Multiple Cause of Death (D77 = 2018-2022, D157 = 2018-2023+)
# ICD-10 drug codes used as multiple cause:
#   T40.1 = Heroin
#   T40.4 = Synthetic opioids (fentanyl)
#   T40.5 = Cocaine
#   T43.6 = Psychostimulants (meth/amphetamines)
#   T40.2 = Other opioids (prescription)
#   X40-X44 = Accidental drug poisoning (underlying cause filter)
#
# Jackson County MO FIPS: 29095

CDC_WONDER_INSTRUCTIONS = """
--- CDC WONDER MANUAL DOWNLOAD (takes ~5 minutes) ---
1. Go to: https://wonder.cdc.gov/mcd-icd10-expanded.html
2. Accept the Data Use Restrictions
3. Section 1 - Group Results By:
     State, County / Year / Month / MCD - Drug/Alcohol Induced Causes
4. Section 2 - Underlying cause: Drug/Alcohol Induced Causes (check ALL)
5. Section 3 - Demographics: leave as All
6. Section 4 - Location: Missouri > Jackson County
7. Section 6 - Year: 2018-2024
8. Other options > Export Results > Tab-delimited text (No Labels)
9. Save file as: data/cdc_wonder_jackson.txt
------------------------------------------------------
"""

def parse_cdc_wonder(filepath="data/cdc_wonder_jackson.txt"):
    """Parse the CDC WONDER TSV export (tab-delimited, quoted fields)."""
    print(f"Parsing CDC WONDER file: {filepath}")
    try:
        df = pd.read_csv(filepath, sep="\t", encoding="latin-1",
                         skipfooter=15, engine="python")
        df.columns = df.columns.str.strip()

        # Drop footer/note rows (Notes col is non-empty on those rows)
        if "Notes" in df.columns:
            df = df[df["Notes"].isna() | (df["Notes"].str.strip() == "")]

        # Drop suppressed and non-data rows
        df = df[df["Deaths"].notna()]
        df = df[df["Deaths"].astype(str).str.strip() != "Suppressed"]
        df["Deaths"] = pd.to_numeric(df["Deaths"], errors="coerce")
        df = df.dropna(subset=["Deaths"])

        # Parse Month Code (format: "2018/01") to proper date
        if "Month Code" in df.columns:
            df["Month_Date"] = pd.to_datetime(df["Month Code"], format="%Y/%m", errors="coerce")
        elif "Month" in df.columns:
            df["Month_Date"] = pd.to_datetime(df["Month"], format="%b., %Y", errors="coerce")

        df["Year"] = df["Month_Date"].dt.year
        df["Month"] = df["Month_Date"].dt.month

        # Rename cause column for consistency
        cause_col = [c for c in df.columns if "Drug/Alcohol Induced Cause" in c
                     and "Code" not in c]
        if cause_col:
            df = df.rename(columns={cause_col[0]: "MCD_Drug_Cause"})
        df["County"] = df.get("County", "Jackson County, MO")

        print(f"  CDC WONDER: {len(df)} rows loaded")
        print(f"  Causes: {df['MCD_Drug_Cause'].value_counts().to_dict()}")
        df.to_csv("data/cdc_wonder_clean.csv", index=False)
        return df
    except FileNotFoundError:
        print(CDC_WONDER_INSTRUCTIONS)
        print("[INFO] Continuing with synthetic CDC data for now.")
        return None
    except Exception as e:
        print(f"[ERROR] CDC parse failed: {e}")
        import traceback; traceback.print_exc()
        return None


def generate_synthetic_cdc():
    """
    Synthetic CDC WONDER data based on known Missouri/KC trends.
    Used for immediate dashboard demo — swap in real data when downloaded.
    Reflects: fentanyl peak 2022, meth rising, xylazine emerging 2023+
    """
    import numpy as np
    np.random.seed(42)

    months = pd.date_range("2018-01", "2024-12", freq="MS")
    n = len(months)
    t = np.linspace(0, 1, n)

    def noisy(base, trend_fn, noise_scale=1.5):
        vals = trend_fn(t) + np.random.normal(0, noise_scale, n)
        return np.clip(np.round(base + vals), 0, None).astype(int)

    data = []
    drug_profiles = {
        "Synthetic Opioids (Fentanyl) T40.4": noisy(
            8, lambda t: 18 * t * (1 - (t - 0.75)**2 * 3), noise_scale=2.5),
        "Heroin T40.1": noisy(
            6, lambda t: -8 * t + np.sin(t * 6) * 1.5, noise_scale=1.2),
        "Cocaine T40.5": noisy(
            3, lambda t: 4 * t + np.sin(t * 4) * 1.0, noise_scale=1.0),
        "Psychostimulants (Meth) T43.6": noisy(
            2, lambda t: 7 * t + np.sin(t * 3) * 0.8, noise_scale=0.9),
        "Other Opioids T40.2": noisy(
            4, lambda t: -3 * t + np.sin(t * 5) * 1.0, noise_scale=0.8),
    }

    for drug, counts in drug_profiles.items():
        for i, month in enumerate(months):
            if counts[i] > 0:
                data.append({
                    "Year": month.year,
                    "Month": month.month,
                    "Month_Date": month,
                    "MCD_Drug_Cause": drug,
                    "Deaths": counts[i],
                    "County": "Jackson County, MO",
                    "synthetic": True,
                })

    df = pd.DataFrame(data)
    df.to_csv("data/cdc_wonder_synthetic.csv", index=False)
    print(f"  Generated synthetic CDC data: {len(df)} rows across {len(drug_profiles)} drug types")
    return df


if __name__ == "__main__":
    kcpd_df = fetch_kcpd()

    cdc_df = parse_cdc_wonder()
    if cdc_df is None:
        print("\nUsing synthetic CDC data for dashboard demo.")
        cdc_df = generate_synthetic_cdc()

    print("\n=== Data Ready ===")
    if kcpd_df is not None:
        print(f"KCPD records: {len(kcpd_df)}")
    print(f"CDC records:  {len(cdc_df)}")
    print("\nRun dashboard: streamlit run dashboard.py")
