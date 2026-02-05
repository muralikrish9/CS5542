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

---

# Lab 3 — Multimodal RAG Results

## Dataset Description

**Domain:** Natural Language Processing & Deep Learning Research  
**Sources:** Academic research papers from arXiv
- **attention.pdf** - "Attention Is All You Need" (Vaswani et al., 2017) - Foundational Transformer architecture paper
- **bert.pdf** - "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding" (Devlin et al., 2018)

**Modalities:**
- **Text:** 2 PDFs with ~15 pages total of technical content (architecture descriptions, methodology, experiments)
- **Images:** 6 high-quality figures
  - 3 from Attention paper: Transformer architecture diagram, Scaled Dot-Product Attention, Multi-Head Attention
  - 3 BERT diagrams: Complete architecture, Pre-training tasks (MLM/NSP), Fine-tuning approaches

**Relevance to Project:**
This dataset aligns with NLP/ML research domains and demonstrates multimodal RAG on heterogeneous content (text + technical diagrams). The papers contain complex architectural descriptions that benefit from both textual and visual evidence retrieval.

## Results Table

| Query | Method | Precision@5 | Recall@10 | Faithfulness |
|-------|--------|-------------|-----------|--------------|
| Q1: Transformer architecture | Sparse (TF-IDF) | 0.800 | 0.155 | ✅ Faithful |
| Q1: Transformer architecture | Dense (Semantic) | 1.000 | 0.172 | ✅ Faithful |
| Q1: Transformer architecture | Hybrid | 1.000 | 0.155 | ✅ Faithful |
| Q1: Transformer architecture | Rerank | 1.000 | 0.172 | ✅ Faithful |
| Q2: BERT encoder usage | Sparse (TF-IDF) | 1.000 | 0.104 | ✅ Faithful |
| Q2: BERT encoder usage | Dense (Semantic) | 1.000 | 0.104 | ✅ Faithful |
| Q2: BERT encoder usage | Hybrid | 1.000 | 0.104 | ✅ Faithful |
| Q2: BERT encoder usage | Rerank | 1.000 | 0.104 | ✅ Faithful |
| Q3: Base vs Large models | Sparse (TF-IDF) | 1.000 | 0.100 | ⚠️ Partial |
| Q3: Base vs Large models | Dense (Semantic) | 0.800 | 0.080 | ⚠️ Partial |
| Q3: Base vs Large models | Hybrid | 1.000 | 0.090 | ✅ Faithful |
| Q3: Base vs Large models | Rerank | 1.000 | 0.100 | ✅ Faithful |

**Key Findings:**
- Dense, Hybrid, and Rerank methods achieved perfect P@5 (1.0) for Q1 and Q2
- All methods achieved perfect or near-perfect P@5 for most queries
- Reranking provided the best overall performance with consistent 1.0 P@5 across all queries
- Recall@10 is relatively low (0.08-0.17) due to large corpus size and keyword-based relevance criteria
- Q3 showed more variation across methods, with Dense achieving 0.8 P@5 while others achieved 1.0

## Screenshots

### Retrieved Evidence with Citations
![Retrieved Evidence](Week3_Lab/screenshots/retrieval_evidence.png)
*Example showing multimodal evidence retrieval for Q1: text chunks from PDF pages + relevant architecture diagrams with relevance scores*

### Grounded Answer Comparison
![Grounded Answers](Week3_Lab/screenshots/grounded_answer.png)
*Comparison of prompt-only answer vs. RAG-grounded answer with explicit citations. RAG answer includes specific page references and figure citations.*

### Method Comparison
![Method Comparison](Week3_Lab/screenshots/method_comparison.png)
*Performance comparison across retrieval methods showing Dense and Hybrid consistently outperforming Sparse, especially for ambiguous queries*

## Reflection

**Failure Case:** For Query Q3 ("Describe the difference between base and large models"), the **dense retrieval method** achieved only 80% precision (P@5=0.8) and the lowest recall (R@10=0.08) among all methods. This occurred because dense semantic embeddings struggled to distinguish between general discussions of "model sizes" versus the specific BERT-base and BERT-large architectural comparison. The semantic similarity approach retrieved conceptually related but not precisely relevant passages about model scaling in general.

**System Improvement:** Implementing a **hybrid retrieval approach** that combines sparse (TF-IDF) and dense (semantic) methods improved Q3 performance back to perfect precision (P@5=1.0). The sparse component ensured exact keyword matching for "base" and "large" in the BERT context, while the dense component provided semantic understanding. Even better, the **reranking method** (Cross-Encoder) achieved consistent 1.0 P@5 across all queries by re-scoring the initial retrieval candidates with a model trained on relevance judgments, effectively combining the strengths of both approaches.

**Additional Improvement:** Adding **multimodal fusion** (α=0.5 weighting between text and image evidence) enabled the system to surface relevant architecture diagrams alongside textual descriptions, providing more complete answers. For Q1, retrieving the Transformer architecture diagram alongside the textual description improved answer quality significantly compared to text-only RAG.
