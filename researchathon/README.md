# AI-Powered Overdose Early Warning System

**CS 5542 · Lab 10 · NSF NRT AI Challenge — Substance Abuse Risk Detection**  
Murali Ediga · University of Missouri–Kansas City · Spring 2026

---

## Demo

[![Watch the demo](https://img.youtube.com/vi/LR7pLWJjRjQ/maxresdefault.jpg)](https://youtu.be/LR7pLWJjRjQ)

---

## Overview

This project predicts **Alcohol-Induced overdose deaths in Jackson County, MO** using KCPD drug arrest volume as a leading indicator — 4 months in advance.

**Core finding:** Drug arrests lead overdose deaths by 4 months (r=0.309, p=0.021, Pearson CCF). A lagged linear regression turns this signal into actionable harm reduction recommendations via a live dashboard with an integrated AI analyst.

---

## Quick Start

```bash
pip install -r requirements.txt
python app.py
# Dashboard → http://localhost:5000
```

The AI analyst (Claude chat) requires a local proxy on port 9999. Without it the dashboard still works — chat will show a connection error.

---

## Project Structure

```
researchathon/
├── app.py                      # Flask app + SSE chat endpoint
├── analyze.py                  # Cross-correlation analysis, CCF, p-values
├── forecast.py                 # Lagged linear regression + alert tiers + VSRR validation
├── fetch_data.py               # KCPD Socrata + CDC VSRR data ingestion
├── dashboard.py                # Dashboard helper utilities
├── templates/
│   └── index.html              # Tailwind CSS dark UI
├── static/
│   └── app.js                  # ApexCharts visualization + chat
├── data/
│   ├── cdc_wonder_clean.csv    # CDC WONDER D157 (2018–2024, ICD-10 T36–T65)
│   ├── kcpd_drug_arrests.csv   # KCPD drug arrests (2020–2024, Socrata)
│   └── vsrr_jackson_county.csv # CDC VSRR provisional 2025 (data_as_of: 2026-01-11)
└── requirements.txt
```

---

## Data Sources

| Dataset | Source | Notes |
|---------|--------|-------|
| KCPD Drug Arrest Records | [Kansas City Open Data](https://data.kcmo.org) · Socrata API | 8,408 records · Jan 2020 – Dec 2024 |
| CDC WONDER D157 Mortality | [wonder.cdc.gov](https://wonder.cdc.gov) · Multiple Cause of Death | ICD-10 T36–T65 · monthly · 2018–2024 |
| CDC VSRR Provisional OD | [data.cdc.gov](https://data.cdc.gov/resource/gb4e-yj24.json) | Rolling 12-mo · Jackson County · through Jun 2025 |

All datasets are public, county-level aggregate, no PII.

---

## Methodology

### 1. Cross-Correlation Function (`analyze.py`)
- Computes Pearson CCF at lags 0–12 months between monthly KCPD arrests and each CDC cause-category death series
- Tests significance with `scipy.stats.pearsonr` (two-tailed, α=0.05)
- **Result: Alcohol-Induced deaths peak at lag=4 (r=0.309, p=0.021)**. No other cause category significant.

### 2. Lagged Linear Regression (`forecast.py`)
```
Deaths(t + 4) = β₀ + β₁ · Arrests(t)
```
- Trained on 2020–2024 (n=56 month pairs)
- β₁=0.00862 · R²=0.007 · std_err=4.3 deaths/mo
- 90% CI: predicted ± 1.645 × std_err
- Alert tiers: NORMAL / MODERATE / ELEVATED / CRITICAL (μ, μ+σ, μ+2σ thresholds)

### 3. 2025 Retrospective Validation
- CDC VSRR provisional data for Jan–Apr 2025 fetched from Socrata
- Model predicted **MODERATE** (21.1/20.9/21.0/21.1 deaths/mo) — no spike
- VSRR confirms: net YoY delta −10 deaths, all-cause rate ≈22/mo ✓

### 4. AI Analyst
- Claude Haiku 4.5 via Flask SSE endpoint
- System prompt includes all model statistics + current forecast
- Natural language Q&A for harm reduction officers

---

## Results

| Metric | Value |
|--------|-------|
| Lead-lag (CCF peak) | **4 months** |
| Pearson r | **0.309** |
| p-value | **0.021** |
| R² | 0.007 |
| Forecast (Jan–Apr 2025) | 21.1 / 20.9 / 21.0 / 21.1 deaths/mo |
| Alert level | **MODERATE** |
| 2025 VSRR YoY delta | **−10 deaths** (declining, no spike) ✓ |

---

## Tech Stack

- Python 3.10 · pandas · NumPy · scipy · scikit-learn
- Flask 3.x · Server-Sent Events (SSE)
- ApexCharts.js · Tailwind CSS
- Anthropic Claude Haiku 4.5 (AI analyst)
- CDC WONDER · KCPD Socrata · CDC VSRR APIs

---

## Ethical Notes

- No individual-level data — all county aggregate
- Arrest data used as supply-disruption proxy, **not** a policing tool
- Model uncertainty (R²=0.007) prominently surfaced in UI and AI responses
- Designed for harm reduction (naloxone, outreach) not law enforcement
