# TRACE: Terminal Recognition and Attribution via Command Entropy

**CS 5542 — Project Assignment 4 (AI/DS Track)**  
**Research-A-Thon 2026**

## Project Description

TRACE is a machine learning system that identifies which Large Language Model (LLM) is driving an autonomous AI agent by analyzing the shell commands it executes on a target system. Using entropy-based features and TF-IDF bigram analysis, TRACE achieves >97% cross-validated accuracy across 7 model families and demonstrates scaffold-invariant generalization to unseen agent frameworks.

### Key Contributions
- **Behavioral fingerprinting**: LLMs have measurably distinct command patterns (lexical diversity, argument entropy, tool usage) that persist across different agent scaffolds
- **Scaffold invariance**: A classifier trained on PentestGPT sessions generalizes to Claude Code (96.7%) without retraining
- **Cross-generation transfer**: Partially transfers to frontier models (Gemini 3.1: 80%, Claude Opus: 70%)
- **DPI resistance**: Deep Prompt Injection attacks do not defeat classification — the model's fingerprint persists even when the agent complies with adversarial payloads
- **Real-time deployment**: Live classifier deployed on a GCP honeypot that fingerprints incoming AI agent sessions in real-time

## Repository Structure

```
Project_Assignment_4/
├── README.md                          # This file
├── TRACE_walkthrough.ipynb            # Main notebook (self-contained walkthrough)
├── data/
│   └── sample/
│       ├── sample_session_gpt4o.json  # Sample session format (GPT-4o)
│       ├── sample_session_claude.json # Sample session format (Claude)
│       └── sample_features.csv        # Sample extracted features
├── models/
│   └── .gitkeep                       # Trained model artifacts (not included)
└── requirements.txt                   # Python dependencies
```

## Dataset Description

**Training data**: 2,230+ sessions across 7 model families and 3 agent scaffolds (PentestGPT, ReAct, Claude Code). Each session contains 10-50 shell commands executed on a Linux honeypot.

**Note**: Raw session data is not included in this repository to preserve anonymity for ongoing research submission. Sample data files are provided to demonstrate the data format and schema. The notebook uses placeholder data for demonstration purposes.

### Data Format
Each session JSON contains:
- `session_id`: Unique identifier
- `family`: Model family label (e.g., `pentestgpt_gpt4o`)
- `scaffold`: Agent framework used
- `entries[]`: Array of command-output pairs with timestamps

### Extracted Features (46 per session)
- **Command statistics**: count, length distribution, entropy
- **Lexical diversity**: unique commands, vocabulary richness
- **Tool usage**: tool call patterns, argument structure
- **Temporal patterns**: inter-command timing
- **Structural features**: session depth, error recovery

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/muralikrish9/CS5542.git
cd CS5542/Project_Assignment_4

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the notebook
jupyter notebook TRACE_walkthrough.ipynb
```

## How to Run

1. Open `TRACE_walkthrough.ipynb` in Jupyter
2. Run all cells top-to-bottom
3. The notebook demonstrates:
   - Data loading and exploration (sample data)
   - Feature extraction pipeline
   - Random Forest classification with cross-validation
   - Confusion matrix and feature importance analysis
   - Cross-generation and scaffold invariance results
   - DPI resistance analysis

## Methodology

1. **Data Collection**: Deploy honeypot, run AI agents (7 model families x 3 scaffolds), capture command logs
2. **Feature Extraction**: Compute 46 entropy/statistical features per session
3. **Classification**: Train Random Forest (200 trees) on feature vectors
4. **Evaluation**: 5-fold stratified CV, LOSO validation, cross-scaffold generalization
5. **Real-time Deployment**: TF-IDF + LinearSVC classifier on GCP VM with 2-minute session aggregation

## Results Summary

| Experiment | Result |
|---|---|
| In-distribution (7 families, 5-fold CV) | F1 > 0.97 |
| Claude Code scaffold invariance | 96.7% (58/60) |
| Gemini 3.1 cross-generation | 80% (16/20) |
| Claude Opus cross-generation | ~70% |
| DPI resistance | Robust (fingerprint survives) |
| Real-time classification | 87% confidence (live demo) |

## Tech Stack
- Python 3.10+, scikit-learn, pandas, numpy, matplotlib, seaborn
- Jupyter Notebook
- GCP (deployment), Docker (honeypot container)

## Team
- Murali Ediga — University of Missouri

## Acknowledgments
Research conducted under Dr. Chatterjee's guidance, CS 5542 Big Data Analytics and Management.
