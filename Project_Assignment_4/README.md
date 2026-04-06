# TRACE: Terminal Recognition and Attribution via Command Entropy

**CS 5542 -- Big Data Analytics and Management | Research-A-Thon 2026**

## Demo Video

[![YouTube Demo](https://img.shields.io/badge/YouTube-Demo%20Video-red?logo=youtube)](https://youtu.be/rBpGjsBFiyI)

Watch the full project walkthrough: **https://youtu.be/rBpGjsBFiyI**

## Project Description

TRACE is a machine learning system that identifies which Large Language Model (LLM) is driving an autonomous AI agent by analyzing the shell commands it executes on a target system. Using TF-IDF bigram features and LinearSVC classification, TRACE achieves high cross-validated accuracy across 7 model families and demonstrates scaffold-invariant generalization to unseen agent frameworks.

## Research Questions

| RQ | Question | Key Result |
|----|----------|------------|
| RQ1 | Can we fingerprint AI agent families from terminal behavior alone? | CV macro-F1 = 0.979 |
| RQ2 | Does the classifier generalize across scaffolds? | LOSO mean = 0.812 |
| RQ3 | Is it robust under evasion and unknown scaffolds? | Vulnetic 78%; mimicry does NOT redirect |
| RQ4 | Does the classifier generalize across model variants? | Control 100%, cross-model 70% |
| RQ5 | Do model families show distinct DPI susceptibility patterns? | deepseek 95% vs claude 0% |

### Key Contributions
- **Behavioral fingerprinting**: 7 LLM families have measurably distinct command patterns that persist across different agent scaffolds
- **Scaffold invariance (LOSO)**: A classifier trained on 2 scaffolds generalizes to the held-out 3rd (mean F1 = 0.812)
- **Evasion robustness**: Mimicry, obfuscation, and timing evasion strategies degrade but do not systematically redirect classification
- **Cross-model transfer**: Behavioral fingerprints persist across model tiers within the same family (Sonnet 4.6 -> Opus 4.6 at 72%)
- **DPI susceptibility profiling**: Model families show distinct, stable susceptibility to Defensive Prompt Injection -- enabling fingerprint-guided targeting
- **Vulnetic blind test**: 78% accuracy on a commercial CTF agent with a proprietary scaffold never seen in training

## Repository Structure

```
Project_Assignment_4/
+-- README.md                          # This file
+-- TRACE_walkthrough.ipynb            # Main notebook (all 5 RQs, self-contained)
+-- build_notebook.py                  # Notebook generator script
+-- data/
|   +-- sample/
|       +-- sample_session_gpt4o.json  # Sample session format (GPT-4o)
|       +-- sample_session_claude.json # Sample session format (Claude)
|       +-- sample_features.csv        # Sample extracted features
+-- models/
|   +-- .gitkeep                       # Trained model artifacts (not included)
+-- requirements.txt                   # Python dependencies
+-- .gitignore
```

## Dataset Description

**Training data**: 1,875 sessions across 7 model families (claude_opus, gpt54, gemini31, deepseek, qwen, kimi, glm5) and 3 agent scaffolds (CC, PGPT, ReAct). Each session contains 10-50 shell commands executed on a Linux honeypot.

**Note**: Raw session data is not included in this repository to preserve anonymity for ongoing research submission. The notebook uses synthetic placeholder data that mirrors the structure and statistical properties of the real dataset to demonstrate the full methodology.

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
2. Run all cells top-to-bottom (`Kernel -> Restart & Run All`)
3. The notebook demonstrates:
   - Synthetic data generation mirroring real session structure
   - TF-IDF + LinearSVC classification pipeline
   - RQ1: 5-fold CV fingerprinting accuracy
   - RQ2: LOSO scaffold generalization with confusion matrices
   - RQ3: Evasion robustness (mimicry, obfuscation, timing) + Vulnetic blind test
   - RQ4: Cross-model generalization (Sonnet 4.6, Gemini 2.5 Flash)
   - RQ5: DPI susceptibility profiling (3 payloads: Vanilla, M2, FC)
   - Feature ablation (verb-only baseline)
   - Classifier comparison (6 classifiers)

## Methodology

1. **Data Collection**: Deploy honeypot, run AI agents (7 families x 3 scaffolds), capture command logs
2. **Feature Extraction**: TF-IDF vectorization of command bigrams (50K features, sublinear TF)
3. **Classification**: LinearSVC with stratified 5-fold CV
4. **Scaffold Generalization**: Leave-One-Scaffold-Out (LOSO) evaluation
5. **Evasion Testing**: Mimicry, obfuscation, timing strategies + Vulnetic blind test
6. **Cross-Model Transfer**: Sonnet 4.6 -> Opus 4.6, Gemini 2.5 -> 3.1
7. **DPI Profiling**: 3 payload conditions (Vanilla, M2 Authority Override, FC Format Coercion)

## Results Summary

| Experiment | Result |
|---|---|
| In-distribution (7 families, 5-fold CV) | F1 = 0.979 |
| LOSO CC held-out | F1 = 0.783 |
| LOSO PGPT held-out | F1 = 0.953 |
| LOSO ReAct held-out | F1 = 0.602 |
| LOSO mean | F1 = 0.812 |
| Vulnetic blind test (unknown scaffold) | 78% (7/9) |
| Cross-model (Sonnet 4.6 -> Opus) | 72% |
| Cross-model (Gemini 2.5 -> 3.1) | 68% |
| DPI: Claude (all payloads) | 0% ASR |
| DPI: DeepSeek (Vanilla) | 95% ASR |

## Tech Stack
- Python 3.10+, scikit-learn, pandas, numpy, matplotlib, seaborn
- Jupyter Notebook
- GCP (deployment), Docker (honeypot container)

## Team
- Murali Ediga -- University of Missouri

## Acknowledgments
Research conducted under Dr. Chatterjee's guidance, CS 5542 Big Data Analytics and Management.
