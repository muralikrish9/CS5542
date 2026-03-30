"""
CS5542 PA3 — Individual Contribution Report Generator
Generates CS5542_PA3_Individual_Report.pdf (1–2 pages).
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib import colors

OUTPUT = os.path.join(os.path.dirname(__file__), "CS5542_PA3_Individual_Report.pdf")


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    )
    ss = getSampleStyleSheet()
    sty_title = ParagraphStyle("T", parent=ss["Title"], fontSize=18, leading=22,
                               spaceAfter=4, textColor=HexColor("#1a1a2e"))
    sty_sub = ParagraphStyle("S", parent=ss["Title"], fontSize=12, leading=15,
                             spaceAfter=4, textColor=HexColor("#16213e"))
    sty_author = ParagraphStyle("A", parent=ss["Normal"], fontSize=11, leading=14,
                                alignment=TA_CENTER, spaceAfter=2)
    sty_head = ParagraphStyle("H", parent=ss["Heading1"], fontSize=13, leading=16,
                              spaceBefore=14, spaceAfter=6, textColor=HexColor("#0f3460"))
    sty_body = ParagraphStyle("B", parent=ss["Normal"], fontSize=10, leading=13,
                              alignment=TA_JUSTIFY, spaceAfter=6)
    hr = HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"),
                    spaceBefore=4, spaceAfter=8)

    story = []

    # Title
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("CS 5542 — PA3 Individual Contribution Report", sty_title))
    story.append(hr)
    story.append(Paragraph("Murali Krishna Goud Ediga", sty_author))
    story.append(Paragraph("Team Promptocalypse | March 31, 2026", sty_author))
    story.append(Spacer(1, 0.2 * inch))

    # Overview
    story.append(Paragraph("Overview", sty_head))
    story.append(Paragraph(
        "As the sole member of Team Promptocalypse, I designed, implemented, tested, and "
        "documented every component of the integrated system across Labs 1–9 and Project "
        "Assignments 2–3. Below is a per-component breakdown of my contributions.",
        sty_body,
    ))

    # Contributions table
    story.append(Paragraph("Contributions by Component", sty_head))

    data = [
        ["Component", "Contribution", "%"],
        ["PA2 — Retrieval Pipeline",
         "Implemented TF-IDF/BM25, dense (all-MiniLM-L6-v2), hybrid, and cross-encoder "
         "reranking. Benchmarked retrieval (+18% MAP). Built Snowflake data pipeline "
         "(500 events, 50 users). Created PA2 report and architecture diagram.", "100%"],
        ["Lab 6 — Agent Integration",
         "Built ReAct agent loop with LLaMA 3.3 70B (Groq). Implemented 5 tools "
         "(query_snowflake, retrieve_documents, compute_statistics, summarize_text, "
         "list_tables). Created Streamlit chat UI. Designed and executed 3-scenario "
         "evaluation (simple/medium/complex). Wrote failure analysis.", "100%"],
        ["Lab 7 — Reproducibility",
         "Created reproduce.sh for single-command execution. Pinned all dependencies. "
         "Implemented deterministic seeding (temp=0, seed=42, PYTHONHASHSEED=42). "
         "Added config.yaml, artifact JSON logging, structured logging. Built offline "
         "smoke test suite. Implemented Reflexion self-critique loop. Wrote REPRO_AUDIT.md "
         "(22/23 items passing).", "100%"],
        ["Lab 8 — Domain Adaptation",
         "Curated 57 instruction-response pairs across 6 cybersecurity sub-domains. "
         "Configured and ran LoRA fine-tuning (rank=16, alpha=32, 3 epochs) on "
         "Llama-3.2-1B-Instruct. Built dual-backend integrated_agent.py supporting "
         "both Groq and local LoRA inference. Designed keyword accuracy evaluation "
         "with 8 test queries.", "100%"],
        ["Lab 9 — Deployment",
         "Built 4-tab Streamlit dashboard (Query Agent, Attack Dashboard, Session Replay, "
         "System Monitor) with Plotly visualizations. Implemented metrics_collector.py "
         "for latency/token/error tracking. Created Dockerfile, docker-compose.yml, and "
         "deploy.sh for containerized deployment.", "100%"],
        ["PA3 — Integration Report",
         "Wrote this integrated system report. Created architecture diagram. Generated "
         "all deliverables programmatically via Python/ReportLab.", "100%"],
    ]

    t = Table(data, colWidths=[1.5 * inch, 3.7 * inch, 0.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("LEADING", (0, 1), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8f8f8"), colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

    # AI Tools
    story.append(Paragraph("AI Tools Used", sty_head))
    story.append(Paragraph(
        "<b>Orion (OpenClaw / Claude Sonnet 4.6)</b> was used as an engineering collaborator "
        "for scaffolding, code generation, and documentation. All generated code was "
        "manually reviewed, tested, and validated. Design decisions, evaluation methodology, "
        "and final correctness were entirely my responsibility.",
        sty_body,
    ))

    story.append(Spacer(1, 0.15 * inch))
    story.append(hr)
    story.append(Paragraph(
        "Generated by Project_Assignment_3/generate_individual_report.py",
        ParagraphStyle("F", parent=ss["Normal"], fontSize=8, alignment=TA_CENTER,
                       textColor=HexColor("#999999")),
    ))

    doc.build(story)
    print(f"Generated: {OUTPUT} ({os.path.getsize(OUTPUT):,} bytes)")


if __name__ == "__main__":
    build_pdf()
