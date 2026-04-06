"""
app.py — Flask backend for KC Drug Market Temporal Analysis Dashboard
Sneat-inspired dark theme + ApexCharts + SSE streaming chat
"""
import os
import sys
import json
import math

from flask import Flask, request, Response, render_template, jsonify, stream_with_context
import pandas as pd
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from analyze import (
    load_kcpd, load_cdc, get_drug_timeseries,
    cross_correlation_analysis, find_all_anomalies, compute_dtw_similarity
)
from forecast import build_forecast

app = Flask(__name__, template_folder='templates', static_folder='static')

# Module-level cache — loaded once per server start
_cache = {}


def _safe(v):
    """Convert numpy/pandas scalars to plain Python for JSON."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if math.isnan(float(v)) else float(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def load_all_cached():
    if 'data' not in _cache:
        data_dir = os.path.join(_HERE, 'data')
        use_synthetic = not os.path.exists(os.path.join(data_dir, 'cdc_wonder_clean.csv'))
        cdc_df = load_cdc(synthetic=use_synthetic)
        drug_ts = get_drug_timeseries(cdc_df)

        try:
            arrests_ts = load_kcpd(os.path.join(data_dir, 'kcpd_drug_arrests.csv'))
        except Exception:
            arrests_ts = None

        xcorr = {}
        if arrests_ts is not None:
            xcorr = cross_correlation_analysis(arrests_ts['Arrests'], drug_ts)

        anomalies = find_all_anomalies(drug_ts, arrests_ts)
        dtw_dist = compute_dtw_similarity(drug_ts)

        fc = None
        if arrests_ts is not None:
            fc = build_forecast(arrests_ts, drug_ts)

        _cache['data'] = (drug_ts, arrests_ts, xcorr, anomalies, dtw_dist, use_synthetic, fc)

    return _cache['data']


def build_data_context(drug_ts, arrests_ts, xcorr, anomalies):
    """Build a text summary of the dataset for Claude's system prompt."""
    lines = []
    lines.append("=== DATASET CONTEXT ===")
    lines.append(f"Region: Jackson County, MO (Kansas City area)")
    lines.append(f"Date range: {drug_ts.index.min().strftime('%B %Y')} to {drug_ts.index.max().strftime('%B %Y')}")
    lines.append(f"Drug death categories: {', '.join(drug_ts.columns.tolist())}")

    if arrests_ts is not None:
        lines.append(f"KCPD drug arrests: {int(arrests_ts['Arrests'].sum())} total records "
                     f"({arrests_ts.index.min().strftime('%b %Y')} - {arrests_ts.index.max().strftime('%b %Y')})")

    lines.append("\n--- Monthly death totals (last 18 months) ---")
    monthly_total = drug_ts.sum(axis=1)
    for date, val in monthly_total.tail(18).items():
        lines.append(f"  {date.strftime('%Y-%m')}: {int(val)} deaths total")

    lines.append("\n--- Per-category death totals (full period) ---")
    for col in drug_ts.columns:
        lines.append(f"  {col}: {int(drug_ts[col].sum())} total, "
                     f"peak {int(drug_ts[col].max())} in {drug_ts[col].idxmax().strftime('%Y-%m')}")

    if xcorr:
        lines.append("\n--- Cross-correlation: KCPD arrests vs. cause-specific deaths ---")
        for drug, res in xcorr.items():
            sig = "SIGNIFICANT (p<0.05)" if res['significant'] else "not significant"
            lines.append(f"  {drug}: {res['interpretation']} | r={res['correlation']}, p={res['p_value']} [{sig}]")

    if not anomalies.empty:
        lines.append("\n--- Top anomalous months (z-score >= 2.0) ---")
        spikes = anomalies[anomalies['direction'] == 'spike'].nlargest(10, 'z_score')
        for _, row in spikes.iterrows():
            lines.append(f"  {row['date'].strftime('%Y-%m')}: {row['source']} spike "
                         f"(z={row['z_score']}, value={int(row['value'])})")
        drops = anomalies[anomalies['direction'] == 'drop'].nsmallest(5, 'z_score')
        for _, row in drops.iterrows():
            lines.append(f"  {row['date'].strftime('%Y-%m')}: {row['source']} DROP "
                         f"(z={row['z_score']}, value={int(row['value'])})")

    return "\n".join(lines)


# ─── ROUTES ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    drug_ts, arrests_ts, xcorr, anomalies, dtw_dist, synthetic, fc = load_all_cached()

    # Deaths time series — ApexCharts [{x: ms_timestamp, y: value}]
    deaths_series = {}
    for col in drug_ts.columns:
        deaths_series[col] = [
            {'x': int(ts.timestamp() * 1000), 'y': _safe(v)}
            for ts, v in zip(drug_ts.index, drug_ts[col])
            if _safe(v) is not None
        ]

    # Arrests time series
    arrests_series = None
    if arrests_ts is not None:
        arrests_series = [
            {'x': int(ts.timestamp() * 1000), 'y': int(v)}
            for ts, v in zip(arrests_ts.index, arrests_ts['Arrests'])
        ]

    # Cross-correlation
    xcorr_data = {}
    for drug, v in xcorr.items():
        xcorr_data[drug] = {
            'lag': int(v['best_lag_months']),
            'r': float(v['correlation']),
            'p': float(v['p_value']),
            'significant': bool(v['significant']),
            'interpretation': v['interpretation'],
        }

    # Anomalies
    anomaly_list = []
    if not anomalies.empty:
        for _, row in anomalies.iterrows():
            anomaly_list.append({
                'date': int(row['date'].timestamp() * 1000),
                'source': row['source'],
                'z_score': float(row['z_score']),
                'value': float(row['value']),
                'direction': row['direction'],
            })

    # DTW heatmap
    dtw_labels = dtw_dist.columns.tolist()
    dtw_matrix = [
        [float(v) if not math.isnan(float(v)) else 0.0 for v in row]
        for row in dtw_dist.values
    ]

    # Calendar heatmap — year x month pivot
    _months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    def _to_calendar(ts_series, col=None):
        """Pivot a time series into {year: {month_abbr: value}}."""
        data = ts_series if col is None else ts_series[col]
        cal = {}
        for date, val in data.items():
            year = str(date.year)
            month = _months[date.month - 1]
            if year not in cal:
                cal[year] = {m: 0 for m in _months}
            v = _safe(val)
            cal[year][month] = v if v is not None else 0
        return cal

    # Deaths: sum all drug categories per month
    deaths_total = drug_ts.sum(axis=1)
    calendar_deaths = _to_calendar(deaths_total)

    calendar_arrests = None
    if arrests_ts is not None:
        calendar_arrests = _to_calendar(arrests_ts['Arrests'])

    # Per-category calendars
    calendar_by_drug = {col: _to_calendar(drug_ts[col]) for col in drug_ts.columns}

    # KPI stats
    date_min = drug_ts.index.min().strftime('%b %Y')
    date_max = drug_ts.index.max().strftime('%b %Y')
    total_deaths = int(drug_ts.sum().sum())
    total_arrests = int(arrests_ts['Arrests'].sum()) if arrests_ts is not None else 0
    sig_corr = sum(1 for v in xcorr.values() if v['significant'])
    n_anomalies = int(len(anomaly_list))

    return jsonify({
        'deaths_series': deaths_series,
        'arrests_series': arrests_series,
        'xcorr': xcorr_data,
        'anomalies': anomaly_list,
        'dtw': {'labels': dtw_labels, 'matrix': dtw_matrix},
        'calendar': {
            'deaths': calendar_deaths,
            'arrests': calendar_arrests,
            'by_drug': calendar_by_drug,
            'months': _months,
        },
        'kpi': {
            'date_range': f'{date_min} - {date_max}',
            'total_deaths': total_deaths,
            'total_arrests': total_arrests,
            'sig_correlations': sig_corr,
            'n_anomalies': n_anomalies,
            'drug_types': len(drug_ts.columns),
        },
        'drug_columns': drug_ts.columns.tolist(),
        'synthetic': synthetic,
        'forecast': fc,
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    body = request.get_json(silent=True) or {}
    user_msg = body.get('message', '').strip()
    history = body.get('history', [])  # [{role, content}, ...]

    if not user_msg:
        return jsonify({'error': 'empty message'}), 400

    drug_ts, arrests_ts, xcorr, anomalies, dtw_dist, synthetic, fc = load_all_cached()
    data_context = build_data_context(drug_ts, arrests_ts, xcorr, anomalies)

    # Build forecast context for the system prompt
    fc_context = ""
    if fc:
        fc_context = f"""
=== PREDICTIVE MODEL (Early Warning System) ===
Model: Lagged linear regression — KCPD arrests at t → {fc['target_col']} deaths at t+{fc['lag_months']} months
Model fit: R²={fc['r2']}, residual std={fc['std_err']} deaths/month
Historical average: {fc['hist_mean']} ± {fc['hist_std']} deaths/month

FORWARD FORECAST (next {len(fc['forecast_labels'])} months):
{chr(10).join(f"  {fc['forecast_labels'][i]}: {fc['predicted'][i]} deaths (90% CI: {fc['lower_90'][i]}–{fc['upper_90'][i]})" for i in range(len(fc['forecast_labels'])))}

Alert level: {fc['alert'].upper()}
System recommendation: {fc['recommendation']}
Predicted next quarter total: {fc['next_quarter_total']} deaths
"""

    system_prompt = f"""You are an AI harm reduction analyst embedded in an early warning dashboard for Jackson County, MO.

Your mission: help public health officials and harm reduction organizations decide WHERE and WHEN to deploy resources — naloxone kits, mobile outreach workers, treatment referrals — to prevent overdose deaths before they happen.

{data_context}
{fc_context}

Core insight driving this system: KCPD drug arrest volume is a LEADING INDICATOR that precedes Alcohol-Induced overdose deaths by 4 months (r=0.309, p=0.021). This means today's arrest data predicts deaths 4 months from now. This 4-month window is the intervention opportunity.

Epidemiological context:
- KC sits on I-70/I-35 corridor — major Midwest drug transit hub
- Supply disruption from enforcement → unknown potency → spike in accidental ODs
- COVID (Mar 2020) disrupted both supply chains AND treatment access simultaneously
- Fentanyl dominance means even small quantity changes cause large lethality swings
- Harm reduction orgs typically need 6–8 weeks lead time to surge resources

When answering:
- Ground every claim in the actual numbers above — cite months, values, z-scores
- Frame answers toward ACTION: not just "deaths spiked" but "this is what it means for resource deployment"
- Give specific, operationalizable recommendations when asked (which neighborhoods, which month, what type of intervention)
- Flag what's statistically solid vs. suggestive
- Use markdown. Be direct and specific."""

    messages = list(history) + [{"role": "user", "content": user_msg}]

    def generate():
        import anthropic
        import time

        client = anthropic.Anthropic(
            base_url="http://127.0.0.1:9999",
            api_key="dummy",
        )

        # Try haiku first (lower rate limits), fall back to sonnet
        models = ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"]
        max_attempts = 3

        for model in models:
            for attempt in range(max_attempts):
                try:
                    with client.messages.stream(
                        model=model,
                        max_tokens=1500,
                        system=system_prompt,
                        messages=messages,
                    ) as stream:
                        for text in stream.text_stream:
                            yield f"data: {json.dumps({'text': text})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                except Exception as e:
                    status = getattr(e, 'status_code', None)
                    if status == 429:
                        if attempt < max_attempts - 1:
                            wait = (attempt + 1) * 5
                            yield f"data: {json.dumps({'text': f'*(rate limited on {model}, retrying in {wait}s...)*'})}\n\n"
                            time.sleep(wait)
                        else:
                            # Try next model
                            break
                    else:
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

        yield f"data: {json.dumps({'error': 'Both models rate-limited. Wait 30s and try again.'})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    print(f"[*] Dashboard starting on http://0.0.0.0:{port}")
    print(f"[*] Data dir: {os.path.join(_HERE, 'data')}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
