from rag_engine import rag

print("Ingesting data...")
rag.ingest_data()

query = "What is the Transformer architecture and how does it differ from RNNs/CNNs?"
print(f"Testing retrieval for: {query}")
results = rag.retrieve(query, top_k_text=5, top_k_images=2, top_k_evidence=8, alpha=0.5, method="sparse")

print(f"Retrieved {len(results)} items.")
for r in results:
    print(f"[{r['modality']}] {r['fused_score']:.3f} - {r['content'][:50]}...")

print("\nTesting evaluation...")
metrics = rag.evaluate_results(query, results)
print(f"Metrics: {metrics}")

if metrics['p5'] == -1.0:
    print("FAILED: Did not match ground truth query.")
else:
    print("PASSED: Evaluation logic works.")

print("Test complete.")
