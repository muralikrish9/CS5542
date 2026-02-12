import os
import csv
import time
from datetime import datetime
import config

def setup_logger():
    """Ensures log file exists with header."""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    if not os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", 
                "query", 
                "retrieval_mode", 
                "latency_sec", 
                "precision_at_5", 
                "recall_at_10", 
                "evidence_ids"
            ])

def log_interaction(query: str, retrieval_mode: str, latency: float, evidence_ids: list, p5: float = -1.0, r10: float = -1.0):
    """Logs a single interaction."""
    timestamp = datetime.now().isoformat()
    
    # Format metrics
    p5_str = f"{p5:.2f}" if p5 >= 0 else "N/A"
    r10_str = f"{r10:.2f}" if r10 >= 0 else "N/A"
    
    with open(config.LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            query[:100].replace("\n", " "), # Truncate and sanitize query
            retrieval_mode,
            f"{latency:.4f}",
            p5_str,
            r10_str,
            ";".join(evidence_ids)
        ])
