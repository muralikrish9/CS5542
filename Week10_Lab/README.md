# CS 5542 — Week 10 Lab: NSF NRT AI Challenge Project

**Team:** Murali Ediga (solo)  
**Due:** April 6, 2026 at 12:00 PM  
**Track:** NRT AI Challenge — Substance Abuse Risk Detection & Temporal Analysis

---

## Demo

[![Watch the demo](https://img.youtube.com/vi/LR7pLWJjRjQ/maxresdefault.jpg)](https://youtu.be/LR7pLWJjRjQ)

---

## Project: AI-Powered Overdose Early Warning System

A live dashboard that uses KCPD drug arrest volume as a **4-month leading indicator** for Alcohol-Induced overdose deaths in Jackson County, MO — enabling proactive naloxone pre-positioning and harm reduction outreach.

### Core Finding

| Metric | Value |
|--------|-------|
| Lead-lag | Arrests → OD deaths by **4 months** |
| Pearson r | **0.309** |
| p-value | **0.021** (significant) |
| Forecast alert | **MODERATE** (Jan–Apr 2025) |
| 2025 validation | YoY delta **−10 deaths** (declining, no spike) ✓ |

---

## Source Code

All code lives in [`../researchathon/`](../researchathon/):

```
researchathon/
├── app.py                    # Flask dashboard (main entry point)
├── analyze.py                # Cross-correlation & statistical analysis
├── forecast.py               # Lagged regression model + VSRR validation
├── fetch_data.py             # KCPD Socrata + CDC VSRR data ingestion
├── dashboard.py              # Dashboard utilities
├── templates/index.html      # Tailwind CSS UI
├── static/app.js             # ApexCharts visualization layer
├── data/
│   ├── cdc_wonder_clean.csv  # CDC WONDER D157 (2018–2024)
│   ├── kcpd_drug_arrests.csv # KCPD Socrata arrests (2020–2024)
│   └── vsrr_jackson_county.csv # CDC VSRR provisional 2025 data
└── requirements.txt
```

---

## Quick Start

```bash
cd ../researchathon
pip install -r requirements.txt
python app.py
# Dashboard at http://localhost:5000
```

The AI analyst requires a Claude proxy running on port 9999:
```bash
python path/to/claude_proxy_v5.py 9999
```

---

## Datasets

| Dataset | Source | Access |
|---------|--------|--------|
| KCPD Drug Arrests | Kansas City Open Data (Socrata) | Public — no key required |
| CDC WONDER D157 Mortality | wonder.cdc.gov (ICD-10 T36–T65) | Public — web query export |
| CDC VSRR Provisional OD | data.cdc.gov/resource/gb4e-yj24.json | Public Socrata API |

All datasets are public, county-level aggregate, and contain no personally identifiable information.

---

## Architecture

```
KCPD Arrests (Socrata API)
  + CDC WONDER D157 Mortality (CSV export)
  ↓
analyze.py — Cross-correlation function (CCF), lag detection
  ↓ lag=4, r=0.309, p=0.021
forecast.py — Lagged linear regression
  ↓ predictions + 90% CI + VSRR validation
app.py (Flask) — SSE streaming
  ↓
index.html + app.js — ApexCharts dashboard
  + Claude Haiku 4.5 AI analyst (natural language Q&A)
```

---

## Key Technical Components

### 1. Cross-Correlation Analysis (`analyze.py`)
- `scipy.signal.correlate` — lags 0–12 months for all cause categories
- `scipy.stats.pearsonr` — two-tailed significance testing (α=0.05)
- Only Alcohol-Induced deaths reached p<0.05 (lag=4, r=0.309)

### 2. Lagged Linear Regression (`forecast.py`)
- `sklearn.linear_model.LinearRegression`
- Training: `(Arrests[t], Deaths[t+4])` pairs, n=56
- Output: 4-month forecast with residual-based 90% CI
- 4-tier alert system: NORMAL → MODERATE → ELEVATED → CRITICAL

### 3. 2025 Retrospective Validation
- Fetched CDC VSRR provisional data for Jan–Jun 2025
- Net YoY delta for Jan–Apr 2025: **−10 deaths** (declining)
- Confirms MODERATE forecast (no spike) — directionally correct

### 4. AI Analyst (Claude Haiku 4.5)
- System prompt contains all model statistics + current forecast
- Flask SSE endpoint + local reverse proxy (port 9999)
- Harm reduction Q&A: naloxone positioning, trend interpretation, uncertainty communication

---

## Deliverables

| File | Description |
|------|-------------|
| `Week10_team_report.pdf` | 4-page project report |
| `Week10_individual_reflection.pdf` | Individual contribution + reflection |
| `../CS5542_KC_Drug_Dashboard.pptx` | 15-slide presentation |
| `../researchathon/` | Full source code |

---

## AI Tools Used

Claude (Anthropic) via OpenClaw assisted with: dashboard code scaffolding, ApexCharts configuration, VSRR data integration, PPT generation. All code manually verified and executed. All analytical decisions (lag selection, model choice, ethical framing) made by the author.
