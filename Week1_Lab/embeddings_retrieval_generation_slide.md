# Mini-RAG System: Embeddings → Retrieval → Generation

## Visual Flow
Raw Data / Documents
        ↓
Embedding Model (Transformer Encoder)
        ↓
Vector Database / Index (FAISS / Pinecone / Snowflake)
        ↓
Retrieved Context
        ↓
LLM (Generation & Reasoning)
        ↓
Final Answer / Decision

## Key Talking Points
- **Embeddings** convert meaning into vectors
- **Retrieval** finds relevant knowledge before the LLM answers
- **Generation** uses retrieved context to reduce hallucination

## Course Connection
- Week 1: Embeddings & Retrieval (Mini-RAG backbone)
- Week 9: Knowledge Graphs & GNNs
- Week 10–12: RAG & GenAI Systems
