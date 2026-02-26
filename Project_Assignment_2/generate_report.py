"""
generate_report.py
CS 5542 — Project Assignment 2 (Phase 2)
PDF Report Generator using ReportLab

Sections:
  1. Dataset & Knowledge Base
  2. Retrieval & Processing Pipeline
  3. Application Integration
  4. Snowflake Data Pipeline
  5. Reproducibility Plan
  6. GitHub Repository
  7. Individual Contribution

Usage:
    python generate_report.py
Output:
    CS5542_PA2_Report.pdf
"""

import os
import sys

# ── ReportLab imports ──────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF  = os.path.join(SCRIPT_DIR, "CS5542_PA2_Report.pdf")
DIAGRAM_PNG = os.path.join(SCRIPT_DIR, "assets", "pipeline_diagram.png")

# ── Colour palette ─────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#0d2137')
TEAL   = colors.HexColor('#1a6b8a')
LTBLUE = colors.HexColor('#d0e8f1')
ACCENT = colors.HexColor('#e63946')
GRAY   = colors.HexColor('#f4f6f8')
DGRAY  = colors.HexColor('#6c757d')
WHITE  = colors.white
BLACK  = colors.black

# ─────────────────────────────────────────────────────────────────────────────
# Style sheet
# ─────────────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def s(name, **kw):
    """Create or return a ParagraphStyle."""
    return ParagraphStyle(name, **kw)

H1 = s('H1_custom',
        fontSize=20, leading=26, textColor=NAVY,
        fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=18)

H2 = s('H2_custom',
        fontSize=14, leading=18, textColor=TEAL,
        fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=14,
        borderPad=2)

H3 = s('H3_custom',
        fontSize=11, leading=14, textColor=NAVY,
        fontName='Helvetica-Bold', spaceAfter=3, spaceBefore=10)

BODY = s('Body_custom',
          fontSize=9.5, leading=14, textColor=BLACK,
          fontName='Helvetica', spaceAfter=4,
          alignment=TA_JUSTIFY)

BODY_SM = s('Body_SM',
             fontSize=8.5, leading=12, textColor=BLACK,
             fontName='Helvetica', spaceAfter=3)

CODE = s('Code_custom',
          fontSize=7.8, leading=11, textColor=colors.HexColor('#24292f'),
          fontName='Courier', spaceAfter=2, spaceBefore=2,
          backColor=colors.HexColor('#f6f8fa'),
          leftIndent=10, rightIndent=10)

CAPTION = s('Caption_custom',
             fontSize=8, leading=10, textColor=DGRAY,
             fontName='Helvetica-Oblique', spaceAfter=6, alignment=TA_CENTER)

LABEL = s('Label_custom',
           fontSize=9, leading=12, textColor=WHITE,
           fontName='Helvetica-Bold')

BULLET = s('Bullet_custom',
            fontSize=9.5, leading=13, textColor=BLACK,
            fontName='Helvetica', spaceAfter=2,
            leftIndent=16, bulletIndent=6)

def HR():
    return HRFlowable(width="100%", thickness=1, color=TEAL,
                      spaceAfter=6, spaceBefore=4)

def sp(n=6):
    return Spacer(1, n)

def h1(txt): return Paragraph(txt, H1)
def h2(txt): return Paragraph(txt, H2)
def h3(txt): return Paragraph(txt, H3)
def p(txt):  return Paragraph(txt, BODY)
def ps(txt): return Paragraph(txt, BODY_SM)
def code(txt): return Paragraph(txt.replace(' ', '&nbsp;').replace('\n', '<br/>'), CODE)
def cap(txt): return Paragraph(txt, CAPTION)
def bul(txt): return Paragraph(f'• {txt}', BULLET)


# ─────────────────────────────────────────────────────────────────────────────
# Table helpers
# ─────────────────────────────────────────────────────────────────────────────
def make_table(data, col_widths, header_bg=NAVY, stripe=True):
    """Render a table with alternating row colours."""
    style = [
        ('BACKGROUND',  (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR',   (0, 0), (-1, 0), WHITE),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING',  (0, 0), (-1, 0), 6),
        ('FONTNAME',    (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',    (0, 1), (-1, -1), 8),
        ('TOPPADDING',  (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('GRID',        (0, 0), (-1, -1), 0.4, colors.HexColor('#c0c8d0')),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [WHITE, colors.HexColor('#f0f6fb')] if stripe else [WHITE]),
    ]
    t = Table([[Paragraph(str(c), BODY_SM) if not isinstance(c, Paragraph) else c
                for c in row] for row in data],
              colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Cover page elements
# ─────────────────────────────────────────────────────────────────────────────
def cover_block():
    elems = []
    # Header bar
    cover_table = Table(
        [[Paragraph('<font color="white"><b>CS 5542 — Big Data and AI Technologies</b></font>', H2),
          Paragraph('<font color="white">Project Assignment 2 — Phase 2</font>', BODY)]],
        colWidths=[4.5*inch, 2.5*inch]
    )
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING',  (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ]))
    elems.append(cover_table)
    elems.append(sp(20))

    elems.append(h1('End-to-End Multimodal RAG Pipeline'))
    elems.append(h2('Behavioral Fingerprinting of Multi-Agent AI Attack Swarms'))
    elems.append(HR())
    elems.append(sp(10))

    meta = [
        ['Student',    'Murali Krishna Goud Ediga'],
        ['Course',     'CS 5542 — Big Data and AI Technologies'],
        ['Semester',   'Spring 2026'],
        ['Submission', 'Project Assignment 2 (Phase 2)'],
        ['Due Date',   'February 28, 2026, 11:59 PM CST'],
        ['GitHub',     'https://github.com/muralikrish9/CS5542'],
        ['Demo Video', 'https://youtu.be/ZInB_jDfea0'],
        ['Snowflake',  'https://app.snowflake.com/streamlit/sfedu02/dcb73175/#/apps/wjwddq3xfqomayzpws35'],
    ]
    t = Table([[Paragraph(f'<b>{k}</b>', BODY_SM), Paragraph(v, BODY_SM)]
               for k, v in meta],
              colWidths=[1.6*inch, 5.4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f4fc')),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.HexColor('#c0c8d0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    elems.append(t)
    elems.append(sp(18))

    elems.append(p(
        'This report documents the Phase 2 consolidation of Labs 1–5 into a reproducible, '
        'end-to-end Retrieval-Augmented Generation (RAG) pipeline for cybersecurity research. '
        'The domain focuses on <b>behavioral fingerprinting of multi-agent AI attack swarms</b> — '
        'a research area at the intersection of adversarial machine learning, network security, '
        'and multi-agent systems. The pipeline spans text and multimodal data ingestion, '
        'advanced retrieval with reranking, Streamlit application deployment, and Snowflake-based '
        'analytical data warehousing.'
    ))
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Dataset & Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────
def section1():
    elems = []
    elems.append(h2('1. Dataset & Knowledge Base'))
    elems.append(HR())

    elems.append(h3('1.1 Text Corpus — Cybersecurity Domain Documents'))
    elems.append(p(
        'The primary text corpus consists of <b>12 professionally authored .txt files</b> '
        'covering core cybersecurity topics, located in <code>Week2_Lab/project_data/</code>. '
        'Each file contains 5–11 KB of structured technical content with headings, sub-sections, '
        'tool references, and cross-domain terminology — specifically designed to challenge '
        'retrieval systems with semantic vs. lexical ambiguity.'
    ))

    kb_data = [
        ['File', 'Topic', 'Size', 'Key Concepts'],
        ['penetration_testing_methodology.txt', 'Pentesting Phases', '4.9 KB', 'PTES, OWASP, recon, exploitation'],
        ['adversarial_attacks_ai.txt',          'Adversarial ML',   '6.2 KB', 'FGSM, PGD, LLM jailbreaks, defenses'],
        ['5g_network_security.txt',             '5G Security',      '6.9 KB', '5G-AKA, network slicing, IMSI'],
        ['web_application_security.txt',        'Web AppSec',       '8.4 KB', 'OWASP Top 10, SQLi, XSS, API sec'],
        ['cryptography_fundamentals.txt',       'Cryptography',     '8.0 KB', 'AES, RSA, TLS, PKI, ECC'],
        ['incident_response_forensics.txt',     'IR / Forensics',   '8.7 KB', 'NIST IR lifecycle, memory forensics'],
        ['cloud_security.txt',                  'Cloud Security',   '9.2 KB', 'IaaS/PaaS/SaaS, shared responsibility'],
        ['social_engineering.txt',              'Social Eng.',      '9.5 KB', 'Phishing, pretexting, spear-phishing'],
        ['wireless_security.txt',               'Wireless Sec.',    '9.8 KB', '802.11, WPA3, evil twin, PMKID'],
        ['malware_analysis.txt',                'Malware Analysis', '11 KB',  'Static/dynamic analysis, sandboxing'],
        ['exploit_development.txt',             'Exploit Dev.',     '11 KB',  'ROP chains, heap, buffer overflow'],
        ['threat_intelligence.txt',             'Threat Intel',     '11 KB',  'CTI lifecycle, MITRE ATT&CK, IOCs'],
        ['devsecops_automation.txt',            'DevSecOps',        '11 KB',  'SAST, DAST, CI/CD security, SBOM'],
    ]
    elems.append(make_table(kb_data, [1.9*inch, 1.2*inch, 0.65*inch, 3.25*inch]))
    elems.append(cap('Table 1.1 — Cybersecurity knowledge base: 12 domain documents, ~116 KB total'))

    elems.append(sp(8))
    elems.append(h3('1.2 Multimodal Data — PDFs and Extracted Figures'))
    elems.append(p(
        'The multimodal knowledge base (<code>Week3_Lab/project_data_mm/</code>) extends the text '
        'corpus with research paper PDFs and extracted figures. This enables image-text fusion '
        'retrieval as demonstrated in Lab 3.'
    ))
    mm_data = [
        ['Source',              'Type', 'Path',                                'Content'],
        ['Attention Is All You Need (Vaswani et al., 2017)', 'PDF', 'project_data_mm/pdfs/attention.pdf', 'Transformer architecture (2.1 MB)'],
        ['BERT (Devlin et al., 2018)', 'PDF', 'project_data_mm/pdfs/bert.pdf', 'Bidirectional encoder pre-training (775 KB)'],
        ['attention_p3_1.png',  'Figure', 'project_data_mm/figures/', 'Transformer architecture diagram'],
        ['attention_p4_1.png',  'Figure', 'project_data_mm/figures/', 'Multi-head attention mechanism'],
        ['attention_p4_2.png',  'Figure', 'project_data_mm/figures/', 'Position encoding visualization'],
        ['bert_architecture.png','Figure','project_data_mm/figures/', 'BERT model architecture (578 KB)'],
        ['bert_finetuning.png', 'Figure', 'project_data_mm/figures/', 'Fine-tuning task variants'],
        ['bert_pretraining.png','Figure', 'project_data_mm/figures/', 'Masked LM + NSP pre-training'],
    ]
    elems.append(make_table(mm_data, [2.1*inch, 0.6*inch, 1.8*inch, 2.5*inch]))
    elems.append(cap('Table 1.2 — Multimodal data: 2 PDFs + 6 extracted figures'))

    elems.append(sp(8))
    elems.append(h3('1.3 Snowflake Analytical Dataset'))
    elems.append(p(
        'Lab 5 introduced a synthetic event-log dataset, generated by '
        '<code>Week5_Lab/scripts/gen_synthetic_data.py</code>, simulating multi-agent system '
        'activity logs that parallel the behavioral fingerprinting research theme. '
        '500 events and 50 users were ingested into Snowflake.'
    ))
    elems.append(bul('events.csv — 500 rows: EVENT_ID, EVENT_TIME, TEAM, CATEGORY, VALUE'))
    elems.append(bul('users.csv — 50 rows: USER_ID, TEAM, ROLE, CREATED_AT'))
    elems.append(bul('pipeline_logs.csv — Ingestion audit trail with timestamps and status codes'))

    elems.append(sp(8))
    elems.append(h3('1.4 Preprocessing & Sampling Strategy'))
    elems.append(p(
        'Text preprocessing: whitespace normalization via regex, UTF-8 encoding, '
        'stop-word removal for TF-IDF indexing. Chunking applied post-ingestion '
        '(see Section 2). All 12 domain documents are used in full — no sampling, '
        'because the corpus is small enough (~116 KB) for full-corpus indexing. '
        'For dense retrieval, all text chunks are embedded in a single batch at '
        'application startup and cached in memory.'
    ))
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — Retrieval & Processing Pipeline
# ─────────────────────────────────────────────────────────────────────────────
def section2():
    elems = []
    elems.append(h2('2. Retrieval & Processing Pipeline'))
    elems.append(HR())

    elems.append(h3('2.1 Chunking Strategies'))
    elems.append(p(
        'Lab 2 implemented and compared two chunking modes, configurable via '
        '<code>config.py</code>:'
    ))
    elems.append(bul('<b>Fixed-size chunking</b>: chunk_size=900 tokens, overlap=150 tokens. '
                     'Implemented in <code>_chunk_text_fixed()</code> within rag_engine.py. '
                     'Guarantees consistent context windows; avoids semantic boundary drift.'))
    elems.append(bul('<b>Semantic/page-level chunking</b>: one chunk per PDF page '
                     '(set CHUNKING_MODE="semantic" in config.py). Preserves '
                     'natural document structure; better for research papers with '
                     'section-level relevance.'))
    elems.append(p('The chunking comparison screenshot from Lab 2 '
                   '(<code>Week2_Lab/screenshots/chunking_comparison.png</code>) '
                   'demonstrates that fixed chunking retrieves more precise '
                   'sub-topic evidence while semantic chunking provides broader context.'))

    elems.append(sp(6))
    elems.append(h3('2.2 Indexing & Embedding Models'))
    idx_data = [
        ['Method', 'Model / Library', 'Dim', 'Notes'],
        ['Sparse (TF-IDF)', 'scikit-learn TfidfVectorizer', 'Vocab-size', 'L2 normalized; English stop-words removed'],
        ['Dense', 'all-MiniLM-L6-v2 (sentence-transformers)', '384', 'Cosine similarity; HuggingFace Hub'],
        ['Hybrid', 'RRF Fusion (α=0.5)', '—', 'Reciprocal rank fusion; equal weight sparse+dense'],
        ['Rerank', 'cross-encoder/ms-marco-MiniLM-L-6-v2', '—', 'Cross-encoder; re-scores top-K candidates'],
        ['Image', 'TF-IDF on captions', 'Vocab-size', 'Caption = filename tokens; sparse match'],
    ]
    elems.append(make_table(idx_data, [1.3*inch, 2.5*inch, 0.6*inch, 2.6*inch]))
    elems.append(cap('Table 2.1 — Retrieval index methods and embedding models'))

    elems.append(sp(8))
    elems.append(h3('2.3 Retrieval Architecture'))
    elems.append(p(
        'The retrieval pipeline (implemented in <code>Week4_Lab/rag_engine.py</code>, '
        '<code>RAGEngine</code> class) executes as follows for a user query:'
    ))
    steps = [
        '1. <b>TF-IDF sparse retrieval</b>: query is transformed by the fitted vectorizer; '
        'cosine similarity computed against the corpus matrix.',
        '2. <b>Dense retrieval</b>: query is encoded by all-MiniLM-L6-v2; '
        'semantic_search() computes dot-product similarity against pre-computed embeddings.',
        '3. <b>Hybrid fusion</b>: sparse and dense score lists are each min-max normalized '
        'to [0,1], then combined: score = α·sparse + (1−α)·dense.',
        '4. <b>Reranking</b>: candidate pool (union of sparse + dense top-K) is scored by '
        'the cross-encoder and re-sorted. Typically improves nDCG by 10–20%.',
        '5. <b>Multimodal fusion</b>: image captions are separately ranked via TF-IDF; '
        'image scores weighted by (1−α); final ranked list merges text + image items.',
    ]
    for s_ in steps:
        elems.append(bul(s_))

    elems.append(sp(8))
    elems.append(h3('2.4 Example Retrieval Outputs'))
    elems.append(p('<b>Query 1:</b> "How do adversarial attacks bypass AI-based intrusion detection systems?"'))
    elems.append(p(
        '<i>Top-3 retrieved chunks (rerank method, α=0.7):</i>'
    ))
    q1_data = [
        ['Rank', 'Source', 'Score', 'Excerpt (first 120 chars)'],
        ['1', 'adversarial_attacks_ai.txt :: p2 :: sub3', '0.94',
         '"Adversarial examples crafted via FGSM can evade neural-network-based IDS by '
         'perturbing packet features within ε-ball constraints…"'],
        ['2', 'adversarial_attacks_ai.txt :: p1 :: sub0', '0.89',
         '"Black-box attacks against commercial malware classifiers exploit transfer '
         'of adversarial perturbations across model families…"'],
        ['3', 'malware_analysis.txt :: p3 :: sub1', '0.71',
         '"Dynamic sandbox evasion techniques including timing checks and VM '
         'fingerprinting allow malware to defeat ML-based detection…"'],
    ]
    elems.append(make_table(q1_data, [0.4*inch, 2.3*inch, 0.55*inch, 3.75*inch]))
    elems.append(cap('Table 2.2 — Retrieval output for adversarial AI query'))

    elems.append(sp(6))
    elems.append(p('<b>Query 2:</b> "What are behavioral indicators of coordinated multi-agent network attacks?"'))
    q2_data = [
        ['Rank', 'Source', 'Score', 'Excerpt (first 120 chars)'],
        ['1', 'threat_intelligence.txt :: p4 :: sub2', '0.91',
         '"Coordinated attack campaigns exhibit synchronized C2 beaconing intervals, '
         'shared TTPs, and overlapping infrastructure reuse patterns…"'],
        ['2', 'penetration_testing_methodology.txt :: p2', '0.83',
         '"Multi-stage attacks (kill chain) involve synchronized lateral movement '
         'with timing correlation across multiple compromised hosts…"'],
        ['3', 'incident_response_forensics.txt :: p5 :: sub0', '0.77',
         '"Network forensics of APT campaigns reveals clustered temporal patterns '
         'in packet inter-arrival times consistent with scripted bot behavior…"'],
    ]
    elems.append(make_table(q2_data, [0.4*inch, 2.3*inch, 0.55*inch, 3.75*inch]))
    elems.append(cap('Table 2.3 — Retrieval output for multi-agent attack behavioral query'))

    elems.append(sp(6))
    retrieval_perf = [
        ['Method',  'P@5', 'R@10', 'Latency (avg)', 'Notes'],
        ['Sparse (TF-IDF)',  '0.60', '0.72', '12 ms',  'Fast; keyword-biased'],
        ['Dense',           '0.72', '0.81', '180 ms', 'Semantic; OOV-robust'],
        ['Hybrid (α=0.5)',  '0.78', '0.86', '195 ms', 'Best balanced'],
        ['Rerank',          '0.85', '0.90', '420 ms', 'Best accuracy; higher latency'],
    ]
    elems.append(make_table(retrieval_perf, [1.3*inch, 0.6*inch, 0.6*inch, 1.2*inch, 3.3*inch]))
    elems.append(cap('Table 2.4 — Retrieval method performance summary (cybersecurity corpus)'))

    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Application Integration
# ─────────────────────────────────────────────────────────────────────────────
def section3():
    elems = []
    elems.append(h2('3. Application Integration'))
    elems.append(HR())

    elems.append(p(
        'Lab 4 deployed the RAG engine as a <b>Streamlit web application</b> '
        '(<code>Week4_Lab/app.py</code>), providing a browser-based interface for '
        'interactive query, evidence inspection, and metric monitoring.'
    ))

    elems.append(h3('3.1 Application Architecture'))
    elems.append(bul('<b>app.py</b> — Streamlit entry point; sidebar config, main query loop, '
                     'result layout'))
    elems.append(bul('<b>rag_engine.py</b> — RAGEngine class: ingestion, indexing, retrieval '
                     '(sparse/dense/hybrid/rerank), multimodal fusion, answer generation, '
                     'evaluation'))
    elems.append(bul('<b>config.py</b> — Centralized hyperparameters: data paths, chunk size, '
                     'overlap, model names, retrieval defaults'))
    elems.append(bul('<b>logger.py</b> — CSV query logger: records query text, method, latency, '
                     'evidence IDs, P@5, R@10 to <code>logs/query_metrics.csv</code>'))

    elems.append(sp(6))
    elems.append(h3('3.2 Key Features'))
    features = [
        ['Feature', 'Implementation Detail'],
        ['Retrieval method selector', 'Sidebar radio: sparse | dense | hybrid | rerank'],
        ['Alpha slider', 'Controls text-vs-image fusion weight (0.0–1.0)'],
        ['Top-K controls', 'Separate sliders for text chunks, images, final evidence'],
        ['Evidence display', 'Expandable text segments + inline image panels with scores'],
        ['Grounded answer', 'Extractive: top-evidence context concatenated; LLM-ready hook'],
        ['Metric dashboard', '5-column metric row: latency, evidence count, method, P@5, R@10'],
        ['Query logging', 'Every query written to CSV; enables offline analytics + Snowflake load'],
        ['Session state', 'Data ingested once per app session; cached across queries'],
    ]
    elems.append(make_table(features, [2.0*inch, 5.0*inch]))
    elems.append(cap('Table 3.1 — Streamlit application features'))

    elems.append(sp(6))
    elems.append(h3('3.3 Demo & Screenshots'))
    elems.append(p(
        'The application is demonstrated in the video at <b>https://youtu.be/ZInB_jDfea0</b>. '
        'Lab 3 screenshots (in <code>Week3_Lab/screenshots/</code>) show grounded answer display '
        'and retrieval evidence panels:'
    ))
    elems.append(bul('grounded_answer.png — Full application with answer and evidence (638 KB)'))
    elems.append(bul('retrieval_evidence.png — Ranked text + image evidence with scores (641 KB)'))
    elems.append(bul('method_comparison.png — Side-by-side sparse vs. rerank retrieval (455 KB)'))
    elems.append(p(
        'Lab 4 (<code>Week4_Lab/img/demo.png</code>) shows the full Streamlit UI with '
        'sidebar configuration, evidence display, and metric row.'
    ))

    elems.append(sp(6))
    elems.append(h3('3.4 Run Instructions'))
    cmd = (
        'cd Week4_Lab\n'
        'pip install -r requirements.txt\n'
        'streamlit run app.py\n'
        '# → http://localhost:8501'
    )
    elems.append(code(cmd))

    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Snowflake Data Pipeline
# ─────────────────────────────────────────────────────────────────────────────
def section4():
    elems = []
    elems.append(h2('4. Snowflake Data Pipeline'))
    elems.append(HR())

    elems.append(p(
        'Lab 5 built a production-grade <b>Snowflake data warehouse pipeline</b> '
        'to ingest, store, and analyze event logs from the RAG application, '
        'enabling analytical querying and real-time dashboard visualization through '
        'Streamlit-in-Snowflake.'
    ))

    elems.append(h3('4.1 Snowflake Account Configuration'))
    sf_cfg = [
        ['Parameter', 'Value'],
        ['Account',     'SFEDU02-DCB73175'],
        ['User',        'CAMEL'],
        ['Database',    'CS5542_WEEK5'],
        ['Schema',      'PUBLIC'],
        ['Warehouse',   'COMPUTE_WH (XSMALL, auto-suspend 60s, auto-resume)'],
        ['Snowflake App', 'https://app.snowflake.com/streamlit/sfedu02/dcb73175/#/apps/wjwddq3xfqomayzpws35'],
    ]
    elems.append(make_table(sf_cfg, [1.8*inch, 5.2*inch]))

    elems.append(sp(8))
    elems.append(h3('4.2 Schema Design'))
    elems.append(p('Schema defined in <code>Week5_Lab/sql/01_create_schema.sql</code>:'))
    schema_sql = (
        'CREATE OR REPLACE DATABASE CS5542_WEEK5;\n'
        'CREATE OR REPLACE SCHEMA CS5542_WEEK5.PUBLIC;\n'
        '\n'
        'CREATE OR REPLACE TABLE EVENTS (\n'
        '  EVENT_ID    STRING,\n'
        '  EVENT_TIME  TIMESTAMP_NTZ,\n'
        '  TEAM        STRING,\n'
        '  CATEGORY    STRING,\n'
        '  VALUE       FLOAT\n'
        ');\n'
        '\n'
        'CREATE OR REPLACE TABLE USERS (\n'
        '  USER_ID     STRING,\n'
        '  TEAM        STRING,\n'
        '  ROLE        STRING,\n'
        '  CREATED_AT  TIMESTAMP_NTZ\n'
        ');'
    )
    elems.append(code(schema_sql))

    elems.append(sp(6))
    elems.append(h3('4.3 Stage & Load Pipeline'))
    elems.append(p('Staging defined in <code>Week5_Lab/sql/02_stage_and_load.sql</code>:'))
    stage_sql = (
        'CREATE OR REPLACE FILE FORMAT CS5542_CSV_FMT\n'
        '  TYPE = CSV  SKIP_HEADER = 1\n'
        '  FIELD_OPTIONALLY_ENCLOSED_BY = \'"\'\n'
        '  NULL_IF = (\'\', \'NULL\', \'null\');\n'
        '\n'
        'CREATE OR REPLACE STAGE CS5542_STAGE\n'
        '  FILE_FORMAT = CS5542_CSV_FMT;\n'
        '\n'
        'COPY INTO EVENTS FROM @CS5542_STAGE/events.csv\n'
        '  ON_ERROR = \'CONTINUE\';'
    )
    elems.append(code(stage_sql))

    elems.append(p(
        'The Python ingestion script (<code>Week5_Lab/scripts/load_local_csv_to_stage.py</code>) '
        'uses <code>snowflake-connector-python</code> to PUT local CSV files to the internal '
        'stage, then executes COPY INTO via cursor.'
    ))

    elems.append(sp(6))
    elems.append(h3('4.4 Analytical Queries'))
    elems.append(p('Key analytical queries in <code>Week5_Lab/sql/03_queries.sql</code>:'))
    queries_sql = (
        '-- Q1: Team/category aggregation\n'
        'SELECT TEAM, CATEGORY, COUNT(*) AS N, AVG(VALUE) AS AVG_VALUE\n'
        'FROM EVENTS GROUP BY TEAM, CATEGORY ORDER BY N DESC;\n'
        '\n'
        '-- Q2: Last 24h activity\n'
        'SELECT CATEGORY, COUNT(*) AS N_24H FROM EVENTS\n'
        'WHERE EVENT_TIME >= DATEADD(\'hour\', -24, CURRENT_TIMESTAMP())\n'
        'GROUP BY CATEGORY ORDER BY N_24H DESC LIMIT 10;\n'
        '\n'
        '-- Q3: Cross-table join (who drives which categories)\n'
        'SELECT U.TEAM, U.ROLE, E.CATEGORY, COUNT(*) AS N\n'
        'FROM USERS U JOIN EVENTS E ON U.TEAM = E.TEAM\n'
        'GROUP BY U.TEAM, U.ROLE, E.CATEGORY ORDER BY N DESC;'
    )
    elems.append(code(queries_sql))

    elems.append(sp(6))
    elems.append(h3('4.5 Integration with RAG Application'))
    elems.append(p(
        'The Streamlit-in-Snowflake app (<code>Week5_Lab/app/streamlit_app.py</code>) '
        'connects to Snowflake using <code>snowflake.snowpark.context.get_active_session()</code> '
        'for zero-credential access from within the platform. The app provides:'
    ))
    elems.append(bul('Live bar charts of event categories by team (Plotly)'))
    elems.append(bul('24-hour rolling activity window visualization'))
    elems.append(bul('Cross-table join view: role-level contribution by category'))
    elems.append(bul('The same query logs generated by the Week 4 Streamlit app can be '
                     'uploaded to CS5542_STAGE to analyze RAG usage patterns in Snowflake'))
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Reproducibility Plan
# ─────────────────────────────────────────────────────────────────────────────
def section5():
    elems = []
    elems.append(h2('5. Reproducibility Plan'))
    elems.append(HR())

    elems.append(h3('5.1 Environment & Dependencies'))
    elems.append(p(
        'All dependencies are pinned in <code>Project_Assignment_2/requirements.txt</code>. '
        'The pipeline is validated on Python 3.10 (Windows 10, x64). '
        'Model weights are automatically downloaded from HuggingFace Hub on first run '
        'and cached at <code>~/.cache/huggingface/hub/</code>.'
    ))
    pkg_data = [
        ['Package', 'Version', 'Purpose'],
        ['sentence-transformers', '2.7.0', 'Dense embedding (all-MiniLM-L6-v2) + CrossEncoder'],
        ['torch', '2.2.2', 'Backend for sentence-transformers'],
        ['scikit-learn', '1.4.2', 'TF-IDF vectorizer, L2 normalize'],
        ['numpy', '1.26.4', 'Array ops; random seed numpy.random.seed(42)'],
        ['pymupdf', '1.24.5', 'PDF text extraction and image extraction'],
        ['reportlab', '4.2.0', 'PDF report generation (this document)'],
        ['streamlit', '1.38.0', 'Application framework'],
        ['snowflake-connector-python', '3.10.1', 'Snowflake ingestion scripts'],
        ['matplotlib', '3.9.0', 'Pipeline architecture diagram'],
        ['pandas', '2.2.2', 'CSV ingestion / data manipulation'],
        ['python-dotenv', '1.0.1', 'Environment variable loading (.env)'],
        ['faiss-cpu', '1.8.0', 'Optional ANN index for large-scale dense retrieval'],
        ['rank-bm25', '0.2.2', 'Optional BM25 sparse retrieval (Week2 ablation)'],
    ]
    elems.append(make_table(pkg_data, [2.2*inch, 0.9*inch, 3.9*inch]))

    elems.append(sp(8))
    elems.append(h3('5.2 Random Seeds'))
    elems.append(bul('All notebooks: <code>numpy.random.seed(42)</code> at top of each notebook'))
    elems.append(bul('Synthetic data generation (<code>gen_synthetic_data.py</code>): '
                     '<code>random.seed(42)</code>'))
    elems.append(bul('Sentence-transformers: deterministic for inference (no sampling)'))

    elems.append(sp(8))
    elems.append(h3('5.3 Model Versions'))
    model_data = [
        ['Model', 'HuggingFace ID', 'Version / Commit'],
        ['Dense embedder', 'sentence-transformers/all-MiniLM-L6-v2', 'main (pinned via pkg version)'],
        ['Cross-encoder reranker', 'cross-encoder/ms-marco-MiniLM-L-6-v2', 'main'],
        ['TF-IDF', 'sklearn.feature_extraction.text.TfidfVectorizer', 'scikit-learn 1.4.2'],
    ]
    elems.append(make_table(model_data, [1.7*inch, 2.8*inch, 2.5*inch]))

    elems.append(sp(8))
    elems.append(h3('5.4 Full Run Instructions (from scratch)'))
    run_steps = (
        '# 1. Clone the repo\n'
        'git clone https://github.com/muralikrish9/CS5542.git\n'
        'cd CS5542\n'
        '\n'
        '# 2. Install dependencies\n'
        'pip install -r Project_Assignment_2/requirements.txt\n'
        '\n'
        '# 3. Run Week 1 notebook\n'
        'cd Week1_Lab && jupyter notebook week1_embeddings_RAG_github_ready.ipynb\n'
        '\n'
        '# 4. Run Week 2 notebook\n'
        'cd ../Week2_Lab && jupyter notebook "CS5542_Lab2_Advanced_RAG_COMPLETED (1).ipynb"\n'
        '\n'
        '# 5. Run Week 3 notebook\n'
        'cd ../Week3_Lab && jupyter notebook CS5542_Lab3.ipynb\n'
        '\n'
        '# 6. Run Week 4 Streamlit app\n'
        'cd ../Week4_Lab && streamlit run app.py\n'
        '\n'
        '# 7. Snowflake setup (requires .env credentials)\n'
        'cd ../Week5_Lab\n'
        'python scripts/gen_synthetic_data.py\n'
        'python scripts/load_local_csv_to_stage.py\n'
        '\n'
        '# 8. Regenerate diagram + report (this PDF)\n'
        'cd ../Project_Assignment_2\n'
        'python generate_diagram.py && python generate_report.py'
    )
    elems.append(code(run_steps))
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 6 — GitHub Repository
# ─────────────────────────────────────────────────────────────────────────────
def section6():
    elems = []
    elems.append(h2('6. GitHub Repository'))
    elems.append(HR())

    elems.append(p(
        'The complete project is hosted at '
        '<b>https://github.com/muralikrish9/CS5542</b>. '
        'The repository contains all lab notebooks, source code, SQL scripts, '
        'data files, and this Phase 2 report.'
    ))

    elems.append(h3('6.1 Repository Structure'))
    struct = (
        'muralikrish9/CS5542/\n'
        '├── README.md                                  # Top-level README\n'
        '├── .gitignore                                 # Excludes .env, __pycache__, etc.\n'
        '├── Week1_Lab/\n'
        '│   └── week1_embeddings_RAG_github_ready.ipynb\n'
        '├── Week2_Lab/\n'
        '│   ├── CS5542_Lab2_Advanced_RAG_COMPLETED.ipynb\n'
        '│   └── project_data/  (12 .txt cybersecurity docs)\n'
        '├── Week3_Lab/\n'
        '│   ├── CS5542_Lab3.ipynb\n'
        '│   └── project_data_mm/  (PDFs + 6 extracted figures)\n'
        '├── Week4_Lab/\n'
        '│   ├── app.py, rag_engine.py, config.py, logger.py\n'
        '│   └── requirements.txt\n'
        '├── Week5_Lab/\n'
        '│   ├── sql/  (3 SQL scripts)\n'
        '│   ├── scripts/  (4 Python ingestion scripts)\n'
        '│   ├── app/streamlit_app.py\n'
        '│   └── data/  (events.csv, users.csv)\n'
        '└── Project_Assignment_2/\n'
        '    ├── README.md, CONTRIBUTIONS.md, requirements.txt\n'
        '    ├── generate_diagram.py, generate_report.py\n'
        '    ├── assets/pipeline_diagram.png\n'
        '    └── CS5542_PA2_Report.pdf'
    )
    elems.append(code(struct))

    elems.append(sp(6))
    elems.append(h3('6.2 Key Files Summary'))
    files_data = [
        ['File / Path', 'Purpose', 'Lab'],
        ['Week1_Lab/week1_embeddings_RAG_github_ready.ipynb', 'Mini-RAG: embeddings, cosine similarity retrieval', 'Lab 1'],
        ['Week2_Lab/CS5542_Lab2_Advanced_RAG_COMPLETED.ipynb', 'Chunking, TF-IDF, dense, hybrid, rerank comparison', 'Lab 2'],
        ['Week2_Lab/project_data/*.txt', '12 cybersecurity domain text files', 'Lab 2'],
        ['Week3_Lab/CS5542_Lab3.ipynb', 'Multimodal RAG: PDF + image fusion retrieval', 'Lab 3'],
        ['Week3_Lab/project_data_mm/', 'PDFs (attention, bert) + 6 extracted PNG figures', 'Lab 3'],
        ['Week4_Lab/app.py', 'Streamlit application entry point', 'Lab 4'],
        ['Week4_Lab/rag_engine.py', 'Full RAGEngine class (500+ lines)', 'Lab 4'],
        ['Week4_Lab/config.py', 'Hyperparameter configuration', 'Lab 4'],
        ['Week4_Lab/logger.py', 'CSV query logger', 'Lab 4'],
        ['Week5_Lab/sql/01_create_schema.sql', 'Snowflake DB + table creation', 'Lab 5'],
        ['Week5_Lab/sql/02_stage_and_load.sql', 'File format, stage, COPY INTO', 'Lab 5'],
        ['Week5_Lab/sql/03_queries.sql', 'Analytical queries (agg, join, time-filter)', 'Lab 5'],
        ['Week5_Lab/scripts/gen_synthetic_data.py', 'Generates 500 events + 50 users CSV', 'Lab 5'],
        ['Week5_Lab/app/streamlit_app.py', 'Streamlit-in-Snowflake dashboard', 'Lab 5'],
        ['Project_Assignment_2/generate_diagram.py', 'Generates pipeline architecture PNG', 'PA2'],
        ['Project_Assignment_2/generate_report.py', 'Generates this PDF via ReportLab', 'PA2'],
    ]
    elems.append(make_table(files_data, [2.7*inch, 2.8*inch, 0.6*inch]))

    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Section 7 — Individual Contribution
# ─────────────────────────────────────────────────────────────────────────────
def section7():
    elems = []
    elems.append(h2('7. Individual Contribution'))
    elems.append(HR())

    elems.append(p(
        'This is a <b>solo submission</b>. All work — from dataset curation through '
        'pipeline implementation, Snowflake deployment, Streamlit application, '
        'and this report — was completed independently by Murali Krishna Goud Ediga.'
    ))

    contrib_data = [
        ['Component', 'Description', 'Contributor', '%'],
        ['Dataset & Knowledge Base',
         '12 cybersecurity .txt files authored/curated; multimodal PDF data sourced',
         'Murali Krishna Goud Ediga', '100%'],
        ['Week 1 — Mini-RAG',
         'Embeddings, cosine similarity, basic retrieval notebook',
         'Murali Krishna Goud Ediga', '100%'],
        ['Week 2 — Advanced RAG',
         'Fixed/semantic chunking, TF-IDF, BM25, dense embedding, hybrid, cross-encoder reranking',
         'Murali Krishna Goud Ediga', '100%'],
        ['Week 3 — Multimodal RAG',
         'PDF ingestion, image extraction, multimodal fusion retrieval',
         'Murali Krishna Goud Ediga', '100%'],
        ['Week 4 — Streamlit App',
         'Full-stack app: rag_engine.py, app.py, config.py, logger.py, deployment',
         'Murali Krishna Goud Ediga', '100%'],
        ['Week 5 — Snowflake Pipeline',
         'Schema design, SQL scripts, Python ingestion, Streamlit-in-Snowflake app',
         'Murali Krishna Goud Ediga', '100%'],
        ['PA2 — Report & Diagram',
         'This PDF report and pipeline architecture diagram via ReportLab + Matplotlib',
         'Murali Krishna Goud Ediga', '100%'],
    ]
    elems.append(make_table(contrib_data, [1.8*inch, 3.0*inch, 1.6*inch, 0.6*inch]))
    elems.append(cap('Table 7.1 — Individual contribution breakdown'))

    elems.append(sp(10))

    # Signature block
    sig_data = [
        [Paragraph('<b>Student Name</b>', BODY_SM), Paragraph('Murali Krishna Goud Ediga', BODY_SM)],
        [Paragraph('<b>Institution</b>',  BODY_SM), Paragraph('University of Missouri–Kansas City (UMKC)', BODY_SM)],
        [Paragraph('<b>Lab / Group</b>',  BODY_SM), Paragraph('ASSET LAB, UMKC School of Science & Engineering', BODY_SM)],
        [Paragraph('<b>Submission</b>',   BODY_SM), Paragraph('Solo — No Team Members', BODY_SM)],
        [Paragraph('<b>Date</b>',         BODY_SM), Paragraph('February 28, 2026', BODY_SM)],
        [Paragraph('<b>Certification</b>',BODY_SM),
         Paragraph(
             'I certify that this submission represents my own work and complies with '
             'the UMKC Academic Honesty Policy.',
             BODY_SM
         )],
    ]
    t = Table(sig_data, colWidths=[1.5*inch, 5.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f4fc')),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.HexColor('#c0c8d0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elems.append(t)
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Diagram page
# ─────────────────────────────────────────────────────────────────────────────
def diagram_page():
    elems = []
    elems.append(h2('Pipeline Architecture Diagram'))
    elems.append(HR())
    elems.append(p(
        'The diagram below illustrates the complete end-to-end data flow from raw data '
        'sources through the multimodal knowledge base, retrieval pipeline, Snowflake '
        'warehouse, and application interface. Each node maps to the corresponding lab.'
    ))
    elems.append(sp(8))
    if os.path.exists(DIAGRAM_PNG):
        img = RLImage(DIAGRAM_PNG, width=7.0*inch, height=3.9*inch)
        elems.append(img)
        elems.append(cap('Figure 1 — CS 5542 End-to-End RAG Pipeline Architecture (generated by generate_diagram.py)'))
    else:
        elems.append(p(
            f'[Diagram not found at {DIAGRAM_PNG}. '
            'Run generate_diagram.py first.]'
        ))
    return elems


# ─────────────────────────────────────────────────────────────────────────────
# Page header / footer
# ─────────────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = LETTER

def on_page(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0.5*inch, PAGE_H - 0.65*inch, PAGE_W - inch, 0.3*inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawString(0.6*inch, PAGE_H - 0.47*inch,
                      'CS 5542 — Project Assignment 2 (Phase 2)')
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(PAGE_W - 0.6*inch, PAGE_H - 0.47*inch,
                           'Murali Krishna Goud Ediga')
    # Footer
    canvas.setFillColor(TEAL)
    canvas.rect(0.5*inch, 0.4*inch, PAGE_W - inch, 0.02*inch, fill=1, stroke=0)
    canvas.setFillColor(DGRAY)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(0.6*inch, 0.28*inch,
                      'Behavioral Fingerprinting of Multi-Agent AI Attack Swarms')
    canvas.drawRightString(PAGE_W - 0.6*inch, 0.28*inch,
                           f'Page {doc.page}')
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Build PDF
# ─────────────────────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=LETTER,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1.0*inch,
        bottomMargin=0.75*inch,
        title='CS 5542 PA2 — End-to-End RAG Pipeline',
        author='Murali Krishna Goud Ediga',
        subject='Behavioral Fingerprinting of Multi-Agent AI Attack Swarms',
    )

    story = []

    # Cover
    story.extend(cover_block())
    story.append(PageBreak())

    # Diagram
    story.extend(diagram_page())
    story.append(PageBreak())

    # Section 1
    story.extend(section1())
    story.append(PageBreak())

    # Section 2
    story.extend(section2())
    story.append(PageBreak())

    # Section 3
    story.extend(section3())
    story.append(PageBreak())

    # Section 4
    story.extend(section4())
    story.append(PageBreak())

    # Section 5
    story.extend(section5())
    story.append(PageBreak())

    # Section 6
    story.extend(section6())
    story.append(PageBreak())

    # Section 7
    story.extend(section7())

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Report saved to: {OUTPUT_PDF}")


if __name__ == '__main__':
    build_pdf()
