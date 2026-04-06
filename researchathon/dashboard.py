"""
dashboard.py — KC Drug Market Pattern Dashboard
Run: streamlit run dashboard.py
"""
import os, sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests, json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from analyze import (
    load_kcpd, load_cdc, get_drug_timeseries,
    cross_correlation_analysis, find_all_anomalies, compute_dtw_similarity
)

# ─── THEME ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="KC Drug Patterns",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }
  .stApp { background-color: #0d0f14; }

  /* Hide Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

  /* KPI cards */
  .kpi-card {
    background: #161b25;
    border: 1px solid #1e2738;
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
  }
  .kpi-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.4rem;
  }
  .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
  }
  .kpi-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.3rem;
  }
  .kpi-accent { color: #e63946; }
  .kpi-teal   { color: #2a9d8f; }

  /* Section headers */
  .section-header {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #475569;
    border-bottom: 1px solid #1e2738;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }

  /* Interpretation card */
  .interp-card {
    background: #0f1520;
    border: 1px solid #1e2738;
    border-left: 3px solid #2a9d8f;
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #94a3b8;
  }
  .interp-card strong { color: #e2e8f0; }
  .interp-card .finding {
    background: #161b25;
    border-radius: 3px;
    padding: 0.6rem 0.9rem;
    margin: 0.6rem 0;
    border-left: 2px solid #e63946;
    color: #cbd5e1;
    font-size: 0.84rem;
  }

  /* Tab styling */
  .stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #1e2738;
    gap: 0;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #475569;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.6rem 1.2rem;
    border: none;
    border-bottom: 2px solid transparent;
  }
  .stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #e2e8f0 !important;
    border-bottom: 2px solid #e63946 !important;
  }

  /* Plot backgrounds */
  .js-plotly-plot .plotly { background: transparent !important; }

  /* Sidebar */
  [data-testid="stSidebar"] { background: #0f1520; border-right: 1px solid #1e2738; }

  /* Selectbox / slider */
  .stSelectbox label, .stSlider label, .stMultiSelect label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #475569;
  }

  /* Warning/info overrides */
  .stAlert { background: #161b25; border-color: #1e2738; }
  div[data-testid="stDataFrame"] { background: #161b25; }
</style>
""", unsafe_allow_html=True)

# ─── PLOT DEFAULTS ────────────────────────────────────────────────────────────

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0f1520",
    font=dict(family="Inter", color="#64748b", size=11),
    margin=dict(t=30, b=30, l=10, r=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#94a3b8"),
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
    ),
    xaxis=dict(gridcolor="#1e2738", zerolinecolor="#1e2738", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#1e2738", zerolinecolor="#1e2738", tickfont=dict(size=10)),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#161b25", bordercolor="#1e2738", font_size=11),
)

DRUG_COLORS = {
    "OD Deaths (Unintentional)": "#e63946",
    "Other Drug-Induced":        "#f4a261",
    "Alcohol-Induced":           "#457b9d",
    "Alcohol OD (X45)":          "#2a9d8f",
    "Drug Arrests":              "#7c3aed",
}

def color(label):
    return DRUG_COLORS.get(label, "#94a3b8")

# ─── DATA ─────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_all():
    from analyze import _data
    use_synthetic = not os.path.exists(_data("cdc_wonder_clean.csv"))
    cdc_df = load_cdc(synthetic=use_synthetic)
    drug_ts = get_drug_timeseries(cdc_df)
    try:
        arrests_ts = load_kcpd()
    except Exception:
        arrests_ts = None
    xcorr = cross_correlation_analysis(arrests_ts["Arrests"], drug_ts) if arrests_ts is not None else {}
    anomalies = find_all_anomalies(drug_ts, arrests_ts)
    dtw_dist = compute_dtw_similarity(drug_ts)
    return drug_ts, arrests_ts, xcorr, anomalies, dtw_dist, use_synthetic

with st.spinner("Loading data..."):
    drug_ts, arrests_ts, xcorr, anomalies, dtw_dist, is_synthetic = load_all()

# ─── AI INTERPRETATION ────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def get_interpretation(xcorr_json, anomaly_count, dtw_json, is_synthetic, _v=2):
    """Call Claude to interpret the findings in plain English."""
    xcorr = json.loads(xcorr_json)
    dtw = json.loads(dtw_json)

    sig = [f"{d}: {r['interpretation']} (r={r['correlation']}, p={r['p_value']})"
           for d, r in xcorr.items() if r.get("significant")]
    nonsig = [f"{d}: {r['interpretation']}" for d, r in xcorr.items() if not r.get("significant")]

    prompt = f"""You are analyzing drug overdose and arrest patterns in Jackson County, Missouri (Kansas City area), 2018-2024.

DATA SUMMARY:
- Significant cross-correlations (p<0.05): {sig if sig else 'None found'}
- Non-significant patterns: {nonsig}
- Anomalous months detected: {anomaly_count}
- DTW similarity (lower = more similar temporal pattern): {dtw}
- Data: {"SYNTHETIC demo data — treat as illustrative only" if is_synthetic else "REAL CDC WONDER + KCPD data"}

Write a concise interpretation (4-6 sentences) of what these patterns suggest about drug market dynamics in KC. Be specific about what the lead-lag relationships mean in practice. Note any limitations. Do NOT use bullet points — write in plain prose. If no significant correlations were found, explain what that absence tells us. Keep it at a researcher's reading level, not a press release."""

    try:
        import anthropic
        client = anthropic.Anthropic(
            base_url="http://127.0.0.1:9999",
            api_key="dummy",
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"[Interpretation unavailable — proxy error: {e}]"

xcorr_json = json.dumps({k: {ik: bool(iv) if hasattr(iv, 'item') else iv for ik, iv in v.items()} for k, v in xcorr.items()})
dtw_json = dtw_dist.round(2).to_json()
n_anomalies = len(anomalies[anomalies["direction"] == "spike"])

# ─── HEADER ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-bottom: 1.8rem;">
  <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#475569;margin-bottom:0.3rem;">
    UMKC · NSF NRT AI Challenge · CS 5542
  </div>
  <div style="font-size:1.6rem;font-weight:700;color:#f1f5f9;line-height:1.1;">
    KC Drug Market Temporal Patterns
  </div>
  <div style="font-size:0.82rem;color:#475569;margin-top:0.3rem;">
    Jackson County, MO · CDC WONDER MCD 2018–2024 · KCPD Open Data 2020–2024
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KPI ROW ──────────────────────────────────────────────────────────────────

total_od = int(drug_ts.get("OD Deaths (Unintentional)", pd.Series([0])).sum())
total_arrests = int(arrests_ts["Arrests"].sum()) if arrests_ts is not None else 0
sig_count = sum(1 for v in xcorr.values() if v.get("significant"))
best = max(xcorr.values(), key=lambda x: abs(x["correlation"]), default=None)

c1, c2, c3, c4 = st.columns(4)
for col, label, val, sub, accent in [
    (c1, "OD Deaths (Unintentional)", f"{total_od:,}", "Jackson Co. 2018–2024", "kpi-accent"),
    (c2, "Drug Arrests", f"{total_arrests:,}", "KCPD 2020–2024", ""),
    (c3, "Significant Lead-Lags", str(sig_count), "p < 0.05", "kpi-teal" if sig_count > 0 else ""),
    (c4, "Anomalous Months", str(n_anomalies), "z-score > 2.0", "kpi-accent" if n_anomalies > 0 else ""),
]:
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value {'kpi-accent' if accent == 'kpi-accent' else 'kpi-teal' if accent == 'kpi-teal' else ''}">{val}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── AI INTERPRETATION ────────────────────────────────────────────────────────

st.markdown('<div class="section-header">AI Interpretation</div>', unsafe_allow_html=True)

with st.spinner("Generating interpretation..."):
    interp = get_interpretation(xcorr_json, n_anomalies, dtw_json, is_synthetic)

findings_html = ""
for d, r in xcorr.items():
    if r.get("significant"):
        findings_html += f'<div class="finding">&#10023; {r["interpretation"]} &nbsp;<code style="font-size:0.78rem;color:#64748b">r={r["correlation"]} · p={r["p_value"]}</code></div>'

synthetic_warn = '<div style="font-size:0.72rem;color:#b45309;margin-top:0.8rem;">&#9888; Based on synthetic data — real CDC download will update this.</div>' if is_synthetic else ''

st.markdown(f"""
<div class="interp-card">
  {interp}
  {findings_html}
  {synthetic_warn}
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "TRENDS", "LEAD–LAG ANALYSIS", "ANOMALY DETECTION", "TEMPORAL SIGNATURES"
])

# ════════════════ TAB 1: TRENDS ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Monthly Death & Arrest Counts</div>', unsafe_allow_html=True)

    focus_cols = [c for c in drug_ts.columns if c not in ["Non-Drug/Alcohol"]]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.62, 0.38],
        vertical_spacing=0.06,
    )

    for col in focus_cols:
        fig.add_trace(go.Scatter(
            x=drug_ts.index, y=drug_ts[col],
            name=col, mode="lines",
            line=dict(color=color(col), width=1.8),
            hovertemplate=f"<b>{col}</b><br>%{{x|%b %Y}}: %{{y}}<extra></extra>",
        ), row=1, col=1)

    # Anomaly markers
    da = anomalies[anomalies["direction"] == "spike"]
    if not da.empty:
        fig.add_trace(go.Scatter(
            x=da["date"], y=[drug_ts.loc[d, focus_cols].max() * 1.05
                              if d in drug_ts.index else 0 for d in da["date"]],
            mode="markers", name="Anomaly",
            marker=dict(symbol="triangle-down", size=8, color="#e63946", opacity=0.7),
            hovertemplate="<b>Anomaly</b><br>%{x|%b %Y}<extra></extra>",
        ), row=1, col=1)

    if arrests_ts is not None:
        fig.add_trace(go.Bar(
            x=arrests_ts.index, y=arrests_ts["Arrests"],
            name="Drug Arrests", marker_color="#7c3aed",
            opacity=0.6,
            hovertemplate="<b>Arrests</b> %{x|%b %Y}: %{y}<extra></extra>",
        ), row=2, col=1)

    layout = PLOT_LAYOUT.copy()
    layout.update(height=500, margin=dict(t=10, b=20, l=10, r=10))
    layout["xaxis2"] = dict(gridcolor="#1e2738", zerolinecolor="#1e2738", tickfont=dict(size=10))
    layout["yaxis2"] = dict(gridcolor="#1e2738", zerolinecolor="#1e2738", tickfont=dict(size=10))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    # YoY table
    st.markdown('<div class="section-header" style="margin-top:1rem;">Year-over-Year Deaths by Category</div>', unsafe_allow_html=True)
    yoy = drug_ts[focus_cols].copy()
    yoy["Year"] = yoy.index.year
    yoy_table = yoy.groupby("Year").sum().astype(int)
    yoy_table["Total"] = yoy_table.sum(axis=1)
    st.dataframe(
        yoy_table.style.background_gradient(cmap="YlOrRd", subset=yoy_table.columns),
        use_container_width=True,
    )

# ════════════════ TAB 2: LEAD-LAG ════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Do Drug Arrests Lead or Follow Overdose Deaths?</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:0.82rem;color:#64748b;margin-bottom:1.2rem;line-height:1.6;">
    Cross-correlation analysis measures whether <strong style="color:#e2e8f0">drug arrest spikes predict future OD deaths</strong>
    (positive lag = arrests are the leading signal) or whether <strong style="color:#e2e8f0">death spikes drive reactive policing</strong>
    (negative lag = deaths precede arrests). The strength of correlation is measured by Pearson r.
    </p>""", unsafe_allow_html=True)

    if not xcorr:
        st.info("No KCPD data loaded.")
    else:
        rows = sorted(xcorr.items(), key=lambda x: abs(x[1]["correlation"]), reverse=True)

        col_a, col_b = st.columns([1, 1])

        with col_a:
            fig2 = go.Figure()
            for drug, res in rows:
                bar_color = "#e63946" if res["best_lag_months"] > 0 else "#2a9d8f"
                sig_marker = "★ " if res["significant"] else ""
                fig2.add_trace(go.Bar(
                    x=[res["best_lag_months"]],
                    y=[f"{sig_marker}{drug}"],
                    orientation="h",
                    marker_color=bar_color,
                    marker_line_width=0,
                    text=f"r={res['correlation']}{'*' if res['significant'] else ''}",
                    textposition="outside",
                    textfont=dict(size=10, color="#94a3b8"),
                    hovertemplate=(
                        f"<b>{drug}</b><br>Lag: {res['best_lag_months']}mo<br>"
                        f"r={res['correlation']} · p={res['p_value']}<extra></extra>"
                    ),
                    showlegend=False,
                ))
            fig2.add_vline(x=0, line=dict(color="#1e2738", width=2))
            layout2 = {k: v for k, v in PLOT_LAYOUT.items() if k not in ("xaxis", "yaxis", "hovermode")}
            layout2.update(
                height=280,
                xaxis=dict(gridcolor="#1e2738", title="Months", tickfont=dict(size=10), zerolinecolor="#1e2738"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10), zerolinecolor="rgba(0,0,0,0)"),
                barmode="overlay",
                margin=dict(t=10, b=40, l=10, r=60),
            )
            fig2.update_layout(**layout2)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("""<div style="font-size:0.7rem;color:#475569;text-align:center">
            <span style="color:#e63946">&#9632;</span> Arrests lead deaths &nbsp;&nbsp;
            <span style="color:#2a9d8f">&#9632;</span> Deaths lead arrests &nbsp;&nbsp;
            <span style="color:#f1f5f9">★</span> p &lt; 0.05
            </div>""", unsafe_allow_html=True)

        with col_b:
            # Table
            table_rows = []
            for drug, res in rows:
                table_rows.append({
                    "Category": drug,
                    "Lag (mo)": res["best_lag_months"],
                    "r": res["correlation"],
                    "p": res["p_value"],
                    "Sig": "Yes *" if res["significant"] else "—",
                })
            df_t = pd.DataFrame(table_rows)
            st.dataframe(
                df_t.style.applymap(
                    lambda v: "color: #2a9d8f; font-weight:600" if v == "Yes *" else "",
                    subset=["Sig"]
                ).applymap(
                    lambda v: f"color: {'#e63946' if isinstance(v, (int, float)) and v > 0 else '#2a9d8f' if isinstance(v, (int, float)) and v < 0 else ''}" ,
                    subset=["Lag (mo)"]
                ),
                use_container_width=True,
                hide_index=True,
            )

# ════════════════ TAB 3: ANOMALIES ═══════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Statistically Anomalous Months (z > 2.0)</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:0.82rem;color:#64748b;margin-bottom:1.2rem;line-height:1.6;">
    Months where death or arrest counts deviate more than 2 standard deviations from the rolling 6-month baseline.
    Spikes may reflect <strong style="color:#e2e8f0">new drug supply events</strong>, bad batches, treatment access disruptions, or COVID-era effects.
    </p>""", unsafe_allow_html=True)

    spikes = anomalies[anomalies["direction"] == "spike"].copy()

    if spikes.empty:
        st.markdown('<div class="interp-card">No anomalous months detected in the current dataset.</div>', unsafe_allow_html=True)
    else:
        fig3 = go.Figure()
        for col in drug_ts.columns:
            fig3.add_trace(go.Scatter(
                x=drug_ts.index, y=drug_ts[col],
                name=col, mode="lines",
                line=dict(color=color(col), width=1.5, dash="dot"),
                opacity=0.4,
                showlegend=True,
                hoverinfo="skip",
            ))

        col_spikes = spikes[spikes["source"].str.startswith("Deaths")]
        fig3.add_trace(go.Scatter(
            x=col_spikes["date"],
            y=col_spikes["z_score"],
            mode="markers",
            name="Death Spike",
            marker=dict(
                size=col_spikes["z_score"] * 6,
                color="#e63946",
                opacity=0.85,
                symbol="circle",
                line=dict(width=1, color="#0d0f14"),
            ),
            yaxis="y2",
            hovertemplate="<b>%{text}</b><br>%{x|%b %Y} · z=%{y:.2f}<extra></extra>",
            text=col_spikes["source"].str.replace("Deaths: ", ""),
        ))

        if arrests_ts is not None:
            arr_spikes = spikes[spikes["source"] == "Drug Arrests"]
            if not arr_spikes.empty:
                fig3.add_trace(go.Scatter(
                    x=arr_spikes["date"], y=arr_spikes["z_score"],
                    mode="markers", name="Arrest Spike",
                    marker=dict(size=arr_spikes["z_score"] * 6, color="#7c3aed",
                                symbol="diamond", opacity=0.85,
                                line=dict(width=1, color="#0d0f14")),
                    yaxis="y2",
                    hovertemplate="<b>Arrest Spike</b><br>%{x|%b %Y} · z=%{y:.2f}<extra></extra>",
                ))

        layout3 = PLOT_LAYOUT.copy()
        layout3.update(
            height=380,
            yaxis=dict(gridcolor="#1e2738", zerolinecolor="#1e2738", tickfont=dict(size=10), title="Deaths"),
            yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                        title="Z-Score", tickfont=dict(size=10)),
            margin=dict(t=10, b=30, l=10, r=60),
        )
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown('<div class="section-header" style="margin-top:1rem;">Anomaly Events Table</div>', unsafe_allow_html=True)
        disp = spikes[["date", "source", "z_score", "value"]].copy()
        disp["date"] = disp["date"].dt.strftime("%b %Y")
        disp.columns = ["Month", "Source", "Z-Score", "Count"]
        disp = disp.sort_values("Z-Score", ascending=False).head(20)
        st.dataframe(disp, use_container_width=True, hide_index=True)

# ════════════════ TAB 4: SIGNATURES ══════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Temporal Pattern Similarity (DTW)</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:0.82rem;color:#64748b;margin-bottom:1.2rem;line-height:1.6;">
    Dynamic Time Warping measures pattern similarity between time series independent of exact timing shifts.
    <strong style="color:#e2e8f0">Low distance = categories share a temporal structure</strong>, suggesting common upstream drivers
    (shared supply network, same user population, co-occurring events).
    </p>""", unsafe_allow_html=True)

    col_c, col_d = st.columns([1, 1])

    with col_c:
        fig4 = go.Figure(go.Heatmap(
            z=dtw_dist.values,
            x=dtw_dist.columns.tolist(),
            y=dtw_dist.index.tolist(),
            colorscale=[[0, "#e63946"], [0.5, "#1e2738"], [1, "#0f1520"]],
            reversescale=True,
            hoverongaps=False,
            hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Distance: %{z:.2f}<extra></extra>",
        ))
        layout4 = {k: v for k, v in PLOT_LAYOUT.items() if k not in ("xaxis", "yaxis", "hovermode")}
        layout4.update(
            height=320,
            xaxis=dict(tickfont=dict(size=9), tickangle=-20),
            yaxis=dict(tickfont=dict(size=9)),
            margin=dict(t=10, b=60, l=10, r=10),
        )
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        fig5 = go.Figure()
        for col in drug_ts.columns:
            s = drug_ts[col]
            s_max = s.max()
            if s_max > 0:
                s = s / s_max
            fig5.add_trace(go.Scatter(
                x=drug_ts.index, y=s,
                name=col, mode="lines",
                line=dict(color=color(col), width=1.8),
                hovertemplate=f"<b>{col}</b><br>%{{x|%b %Y}}: %{{y:.2f}}<extra></extra>",
            ))
        layout5 = PLOT_LAYOUT.copy()
        layout5.update(
            height=320,
            yaxis=dict(gridcolor="#1e2738", zerolinecolor="#1e2738",
                       tickfont=dict(size=10), title="Normalized (0→1)"),
            margin=dict(t=10, b=30, l=10, r=10),
        )
        fig5.update_layout(**layout5)
        st.plotly_chart(fig5, use_container_width=True)

    # Bottom: data note
    data_note = "REAL — CDC WONDER MCD + KCPD Open Data" if not is_synthetic else "SYNTHETIC demo data"
    st.markdown(f"""
    <div style="margin-top:1.5rem;padding:0.8rem 1rem;background:#0f1520;border:1px solid #1e2738;
                border-radius:3px;font-size:0.72rem;color:#475569;font-family:'JetBrains Mono',monospace;">
    DATA SOURCE: {data_note} &nbsp;|&nbsp;
    LOCATION: Jackson County, MO (FIPS 29095) &nbsp;|&nbsp;
    PERIOD: 2018–2024 &nbsp;|&nbsp;
    OD DEFINITION: X40–X44 (Accidental drug poisoning)
    </div>""", unsafe_allow_html=True)
