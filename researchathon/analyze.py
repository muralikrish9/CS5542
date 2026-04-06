"""
analyze.py — Temporal pattern analysis of KC drug market events
Cross-correlation, anomaly detection, and signature clustering
"""
import os
import pandas as pd
import numpy as np
from scipy import stats
from scipy.signal import correlate
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

# Always resolve data paths relative to this file, not the CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "data")


def _data(filename):
    return os.path.join(DATA_DIR, filename)


# ─── LOAD & PREP ─────────────────────────────────────────────────────────────

def load_kcpd(path=None):
    path = path or _data("kcpd_drug_arrests.csv")
    df = pd.read_csv(path, parse_dates=["Reported_Date"])
    df["Month_Date"] = df["Reported_Date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month_Date").size().reset_index(name="Arrests")
    monthly = monthly.set_index("Month_Date").sort_index()
    return monthly


def load_cdc(synthetic=False):
    path = _data("cdc_wonder_synthetic.csv") if synthetic else _data("cdc_wonder_clean.csv")
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        df = pd.read_csv(_data("cdc_wonder_synthetic.csv"))

    df["Month_Date"] = pd.to_datetime(
        df["Year"].astype(str) + "-" + df["Month"].astype(str).str.zfill(2) + "-01"
    )
    return df


def get_drug_timeseries(cdc_df):
    """Pivot CDC data to wide format: index=Month_Date, cols=cause categories, vals=deaths"""
    pivot = cdc_df.pivot_table(
        index="Month_Date", columns="MCD_Drug_Cause", values="Deaths", aggfunc="sum"
    ).fillna(0)
    pivot.index = pd.to_datetime(pivot.index)
    pivot = pivot.sort_index()

    # Shorten column names for display
    rename = {}
    for col in pivot.columns:
        if "Fentanyl" in col or "T40.4" in col:
            rename[col] = "Fentanyl"
        elif "Heroin" in col or "T40.1" in col:
            rename[col] = "Heroin"
        elif "Cocaine" in col or "T40.5" in col:
            rename[col] = "Cocaine"
        elif "Meth" in col or "Stimulant" in col or "T43.6" in col:
            rename[col] = "Meth/Stimulants"
        elif "T40.2" in col or "Other Opioid" in col:
            rename[col] = "Rx Opioids"
        elif "Unintentional" in col or "X40-X44" in col:
            rename[col] = "OD Deaths (Unintentional)"
        elif "All other drug-induced" in col:
            rename[col] = "Other Drug-Induced"
        elif "All other alcohol" in col:
            rename[col] = "Alcohol-Induced"
        elif "non-drug and non-alcohol" in col:
            rename[col] = "Non-Drug/Alcohol"
        elif "Alcohol poisoning" in col or "X45" in col:
            rename[col] = "Alcohol OD (X45)"
        else:
            rename[col] = col[:40]
    pivot = pivot.rename(columns=rename)

    # For analysis focus, drop the non-drug/alcohol causes column if present
    pivot = pivot.drop(columns=["Non-Drug/Alcohol"], errors="ignore")
    return pivot


# ─── CROSS-CORRELATION ───────────────────────────────────────────────────────

def cross_correlation_analysis(arrests_series, deaths_series, max_lag=6):
    """
    Find the lag (in months) at which drug arrests best predict/follow deaths.
    Positive lag = arrests LEAD deaths (arrests precede spikes)
    Negative lag = deaths LEAD arrests (deaths precede arrest response)
    Returns dict of {drug_type: (best_lag, correlation, p_value)}
    """
    results = {}
    # Align on common date range
    common_idx = arrests_series.index.intersection(deaths_series.index)
    if len(common_idx) < 12:
        return results

    a = arrests_series.loc[common_idx].values.astype(float)
    a = (a - a.mean()) / (a.std() + 1e-9)

    for drug in deaths_series.columns:
        d = deaths_series.loc[common_idx, drug].values.astype(float)
        if d.sum() == 0:
            continue
        d = (d - d.mean()) / (d.std() + 1e-9)

        best_r, best_lag, best_p = 0, 0, 1.0
        for lag in range(-max_lag, max_lag + 1):
            if lag > 0:
                a_lag, d_lag = a[lag:], d[:-lag]
            elif lag < 0:
                a_lag, d_lag = a[:lag], d[-lag:]
            else:
                a_lag, d_lag = a, d

            if len(a_lag) < 10:
                continue
            r, p = stats.pearsonr(a_lag, d_lag)
            if abs(r) > abs(best_r):
                best_r, best_lag, best_p = r, lag, p

        results[drug] = {
            "best_lag_months": int(best_lag),
            "correlation": round(float(best_r), 3),
            "p_value": round(float(best_p), 4),
            "significant": bool(best_p < 0.05),
            "interpretation": (
                f"Arrests lead {drug} deaths by {best_lag}mo" if best_lag > 0
                else f"{drug} deaths lead arrests by {abs(best_lag)}mo" if best_lag < 0
                else f"Arrests and {drug} deaths are concurrent"
            )
        }
    return results


# ─── ANOMALY DETECTION ───────────────────────────────────────────────────────

def detect_anomalies(series, window=6, z_thresh=2.0):
    """
    Rolling z-score anomaly detection.
    Returns boolean series — True = anomalous month.
    """
    rolling_mean = series.rolling(window=window, center=True, min_periods=3).mean()
    rolling_std = series.rolling(window=window, center=True, min_periods=3).std()
    z_scores = (series - rolling_mean) / (rolling_std + 1e-9)
    return z_scores.abs() > z_thresh, z_scores


def find_all_anomalies(drug_ts, arrests_ts):
    """Return unified anomaly events across all drug types and arrests."""
    events = []

    for col in drug_ts.columns:
        flags, zscores = detect_anomalies(drug_ts[col])
        for date, is_anomaly in flags.items():
            if is_anomaly:
                events.append({
                    "date": date,
                    "source": f"Deaths: {col}",
                    "z_score": round(zscores[date], 2),
                    "value": drug_ts[col][date],
                    "direction": "spike" if zscores[date] > 0 else "drop",
                })

    if arrests_ts is not None:
        flags, zscores = detect_anomalies(arrests_ts["Arrests"])
        for date, is_anomaly in flags.items():
            if is_anomaly:
                events.append({
                    "date": date,
                    "source": "Drug Arrests",
                    "z_score": round(zscores[date], 2),
                    "value": arrests_ts["Arrests"][date],
                    "direction": "spike" if zscores[date] > 0 else "drop",
                })

    events_df = pd.DataFrame(events).sort_values("date")
    return events_df


# ─── DTW SIGNATURE CLUSTERING ────────────────────────────────────────────────

def compute_dtw_similarity(drug_ts):
    """
    Compute pairwise DTW distance between drug type time series.
    Returns distance matrix as DataFrame.
    """
    try:
        from dtaidistance import dtw
        cols = drug_ts.columns.tolist()
        scaler = StandardScaler()
        scaled = scaler.fit_transform(drug_ts.fillna(0))
        n = len(cols)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = dtw.distance(scaled[:, i], scaled[:, j])
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d
        return pd.DataFrame(dist_matrix, index=cols, columns=cols)
    except ImportError:
        # Fallback: Pearson correlation distance
        corr = drug_ts.corr()
        return 1 - corr.abs()


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run_full_analysis():
    print("Loading data...")
    use_synthetic = not pd.io.common.file_exists("data/cdc_wonder_clean.csv")
    cdc_df = load_cdc(synthetic=use_synthetic)
    drug_ts = get_drug_timeseries(cdc_df)

    try:
        arrests_ts = load_kcpd()
    except FileNotFoundError:
        print("[WARN] No KCPD data found — run fetch_data.py first")
        arrests_ts = None

    print(f"\nDrug types: {list(drug_ts.columns)}")
    print(f"Date range: {drug_ts.index.min()} -> {drug_ts.index.max()}")

    if arrests_ts is not None:
        print("\n=== Cross-Correlation: Arrests vs Deaths ===")
        xcorr = cross_correlation_analysis(arrests_ts["Arrests"], drug_ts)
        for drug, res in xcorr.items():
            sig = "✓" if res["significant"] else "✗"
            print(f"  {sig} {res['interpretation']} (r={res['correlation']}, p={res['p_value']})")

    print("\n=== Anomalous Months ===")
    anomalies = find_all_anomalies(drug_ts, arrests_ts)
    spikes = anomalies[anomalies["direction"] == "spike"].sort_values("z_score", ascending=False)
    print(spikes.head(15).to_string(index=False))

    print("\n=== DTW Signature Similarity ===")
    dtw_dist = compute_dtw_similarity(drug_ts)
    print(dtw_dist.round(2))

    return {
        "drug_ts": drug_ts,
        "arrests_ts": arrests_ts,
        "xcorr": xcorr if arrests_ts is not None else {},
        "anomalies": anomalies,
        "dtw_dist": dtw_dist,
        "synthetic": use_synthetic,
    }


if __name__ == "__main__":
    results = run_full_analysis()
