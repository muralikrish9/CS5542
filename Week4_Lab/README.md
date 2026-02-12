# Lab 4: Multimodal RAG Application

This is a Streamlit-based RAG application for **CS 5542 Lab 4**.
It allows users to search across the "Attention Is All You Need" and "BERT" research papers using both text and image modalities.

## Features
- **Multimodal Retrieval**: Searches both text chunks and image captions.
- **Configurable Settings**: Adjust `Top-K`, `Alpha` (Fusion Weight), and Retrieval Method.
- **Evaluation**: Automatically calculates Precision@5 and Recall@10 for predefined queries.
- **Logging**: Logs all interactions to `logs/query_metrics.csv`.

## Demo
![Application Demo](img/demo.png)

## Setup

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```
   *Note: Requires Python 3.10+.*

2. **Data**:
   The application will automatically download the required PDFs if they are missing from `Week3_Lab/project_data_mm/pdfs`.

## Running the App

Run the application using the helper script:
```bash
./run_app.sh
```

Or manually:
```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. **GitHub**: Push this repository to GitHub.
2. **Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/).
   - Click "New app".
   - Select your repository, branch, and `app.py` as the Main file.
   - Click "Deploy".
3. **Dependencies**: Streamlit Cloud will automatically install packages from `requirements.txt`.
4. **Data**: The application handles data downloading automatically on the first run, so you don't need to commit the PDF files.

## Known Issues
- **Dense Retrieval**: Due to compatibility issues between `transformers` and `torch` on some environments, Dense Retrieval (`dense`/`hybrid`/`rerank` modes) might run in fallback mode. The app gracefully handles this by disabling dense features if imports fail.
- **Latency**: First run involves data ingestion and might take a few seconds.
- **Ephemeral Logs**: On Streamlit Cloud, `logs/query_metrics.csv` is ephemeral (lost on reboot). For permanent logging, connect a database or Google Sheets.

## Logs
Query logs are stored in `logs/query_metrics.csv`.
