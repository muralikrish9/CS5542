Name: Murali Ediga


Major: Comp Sci PhD


Project Interest: Open to any topic that solves a real world issue 

# Lab 2 — Advanced RAG Results

## Dataset
- Domain: Offensive Security & Cybersecurity
- Files: 12 technical documents covering penetration testing, exploit development, malware analysis, 5G security, etc.
- Size: 116 KB total

## Results Summary

| Query | Best Method | Precision@5 | Recall@10 | Why |
|-------|------------|-------------|-----------|-----|
| Q1 (Pentesting phases) | Balanced hybrid (α=0.5) | 0.800 | 0.667 | Structured information benefits from both keyword matching ("phases") and semantic understanding |
| Q2 (ROP technique) | Keyword-heavy (α=0.8) | 0.600 | 0.500 | Technical acronym "ROP" requires exact term matching |
| Q3 (Ambiguous security) | Vector-heavy (α=0.2) | 0.400 | 0.300 | Vague query benefits from semantic expansion |

## Key Findings

1. **Chunking:** Semantic chunking improved precision for conceptual queries by preserving paragraph context
2. **Hybrid Search:** Optimal α varies by query - technical terms need higher α (keyword), concepts need lower α (semantic)
3. **Re-ranking:** Cross-encoder improved relevance by 20-30% on average, especially for Q2
4. **Answer Quality:** RAG-grounded answers were significantly more accurate and detailed than prompt-only

## Failure Case Analysis

**Query:** Q3 ("What security measures protect against attacks?")
**Performance:** Lowest Precision@5 (0.400) and Recall@10 (0.300)

**Which layer failed:**
- **Retrieval layer** - The ambiguous query led to overly broad matches
- Query lacks specificity (which attacks? which context?)
- Retrieval returned chunks about different attack types without clear focus

**System-level fix:**
1. **Query expansion/disambiguation:** Implement a query understanding stage that detects ambiguous queries and either:
   - Ask user for clarification ("Which type of attacks: network, web, social engineering?")
   - Use LLM to generate multiple specific interpretations and retrieve for each
2. **Result clustering:** Group retrieved chunks by topic (web security, network security, etc.) and present organized results
3. **Confidence scoring:** Flag low-confidence retrievals to user when query is too vague

## Screenshots
- Chunking comparison: ![Chunking comparison](Week2_Lab/screenshots/chunking_comparison.png)
- Re-ranking before/after: ![Re-ranking before/after](Week2_Lab/screenshots/reranking_comparison.png)
- Prompt-only vs RAG answers: ![Prompt-only vs RAG answers](Week2_Lab/screenshots/rag_answers_comparison.png)
