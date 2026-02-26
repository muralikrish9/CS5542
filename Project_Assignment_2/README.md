# CS 5542 — Project Assignment 2 (Phase 2)
## End-to-End Multimodal RAG Pipeline
### Topic: Behavioral Fingerprinting of Multi-Agent AI Attack Swarms

---

## Overview

This project consolidates Labs 1–5 into a reproducible end-to-end pipeline for answering cybersecurity research questions using Retrieval-Augmented Generation (RAG). The domain corpus covers penetration testing, malware analysis, adversarial AI, 5G security, and more.

**Student:** Murali Krishna Goud Ediga  
**Course:** CS 5542 – Big Data and AI Technologies  
**Due:** February 28, 2026  
**GitHub:** [muralikrish9/CS5542](https://github.com/muralikrish9/CS5542)  
**Demo Video:** https://youtu.be/ZInB_jDfea0  
**Snowflake App:** https://app.snowflake.com/streamlit/sfedu02/dcb73175/#/apps/wjwddq3xfqomayzpws35

---

## Repository Structure

```
CS5542/
├── Week1_Lab/                          # Mini-RAG with embeddings
│   └── week1_embeddings_RAG_github_ready.ipynb
├── Week2_Lab/                          # Advanced RAG (chunking + reranking)
│   ├── CS5542_Lab2_Advanced_RAG_COMPLETED.ipynb
│   └── project_data/                   # 12 cybersecurity .txt files
├── Week3_Lab/                          # Multimodal RAG
│   ├── CS5542_Lab3.ipynb
│   └── project_data_mm/                # PDFs + extracted figures
├── Week4_Lab/                          # Streamlit app deployment
│   ├── app.py
│   ├── rag_engine.py
│   ├── config.py
│   └── logger.py
├── Week5_Lab/                          # Snowflake data pipeline
│   ├── sql/
│   ├── scripts/
│   └── app/streamlit_app.py
└── Project_Assignment_2/               # THIS FOLDER — Phase 2 report
    ├── README.md
    ├── CONTRIBUTIONS.md
    ├── requirements.txt
    ├── generate_diagram.py             # Pipeline architecture diagram
    ├── generate_report.py              # PDF report generator
    ├── assets/
    │   └── pipeline_diagram.png        # Generated diagram
    └── CS5542_PA2_Report.pdf           # Final submission report
```

---

## Environment Setup

### Prerequisites
- Python 3.10 (at `C:\Users\mural\AppData\Local\Programs\python\Python310\python.exe`)
- Git
- Snowflake account: `SFEDU02-DCB73175`, user `CAMEL`, database `CS5542_WEEK5`

### Install Dependencies
```bash
cd CS5542/Project_Assignment_2
pip install -r requirements.txt
```

### Environment Variables (for Snowflake)
Create a `.env` file in `Week5_Lab/`:
```
SNOWFLAKE_ACCOUNT=SFEDU02-DCB73175
SNOWFLAKE_USER=CAMEL
SNOWFLAKE_PASSWORD=<your_password>
SNOWFLAKE_DATABASE=CS5542_WEEK5
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

---

## Running Each Component

### Week 1 — Mini-RAG
```bash
cd Week1_Lab
jupyter notebook week1_embeddings_RAG_github_ready.ipynb
```

### Week 2 — Advanced RAG
```bash
cd Week2_Lab
jupyter notebook "CS5542_Lab2_Advanced_RAG_COMPLETED (1).ipynb"
```
The notebook uses `project_data/` (12 .txt files). No additional downloads required.

### Week 3 — Multimodal RAG
```bash
cd Week3_Lab
jupyter notebook CS5542_Lab3.ipynb
```
Data: `project_data_mm/pdfs/` (attention.pdf, bert.pdf) + `project_data_mm/figures/` (6 extracted images).

### Week 4 — Streamlit App
```bash
cd Week4_Lab
pip install -r requirements.txt
streamlit run app.py
```
App runs at `http://localhost:8501`. Reads PDFs from `../Week3_Lab/project_data_mm/pdfs/` and images from `../Week3_Lab/project_data_mm/figures/`.

### Week 5 — Snowflake Pipeline
```bash
cd Week5_Lab
# 1. Create schema
snowsql -f sql/01_create_schema.sql
# 2. Stage and load data
python scripts/load_local_csv_to_stage.py
# 3. Run queries
snowsql -f sql/03_queries.sql
```
Live Streamlit-in-Snowflake app: https://app.snowflake.com/streamlit/sfedu02/dcb73175/#/apps/wjwddq3xfqomayzpws35

### Generate Pipeline Diagram
```bash
cd Project_Assignment_2
python generate_diagram.py
```

### Generate PA2 Report PDF
```bash
cd Project_Assignment_2
python generate_report.py
```

---

## Reproducibility

| Component | Version / Seed |
|---|---|
| Python | 3.10.x |
| sentence-transformers | 2.7.0 |
| Dense model | `all-MiniLM-L6-v2` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| TF-IDF | scikit-learn 1.4.2, default params |
| Random seed | `numpy.random.seed(42)` in all notebooks |
| Snowflake warehouse | XSMALL, auto-suspend 60s |

All model weights are downloaded from HuggingFace Hub on first run (cached in `~/.cache/huggingface`).

---

## Key Results

- **Retrieval methods:** Sparse (TF-IDF/BM25), Dense (all-MiniLM-L6-v2), Hybrid, Rerank (cross-encoder)
- **Reranking beats sparse baseline** by ~18% MAP on cybersecurity queries
- **Multimodal fusion** (alpha=0.5) improves diversity of evidence returned
- **Snowflake pipeline** ingests 500 synthetic events + 50 users; supports real-time analytics
- **Demo video:** https://youtu.be/ZInB_jDfea0

---

## Contact

Murali Krishna Goud Ediga — UMKC PhD Student, ASSET LAB  
GitHub: [muralikrish9](https://github.com/muralikrish9)
