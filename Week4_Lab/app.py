import time
import streamlit as st
import config
from rag_engine import rag
from logger import setup_logger, log_interaction

# Page Config
st.set_page_config(
    page_title="Multimodal RAG Lab 4",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Logger
setup_logger()

# Title
st.title("Multimodal RAG Application")
st.markdown("""
This application retrieves context from specific research papers (Attention Is All You Need, BERT) 
using a multimodal approach (Text + Images).
""")

# Sidebar settings
with st.sidebar:
    st.header("Retrieval Configuration")
    
    retrieval_method = st.radio(
        "Retrieval Method",
        ["sparse", "dense", "hybrid", "rerank"],
        index=3,
        help="Select the underlying retrieval strategy."
    )
    
    alpha = st.slider(
        "Alpha (Fusion Weight)", 
        min_value=0.0, max_value=1.0, value=config.DEFAULT_ALPHA, step=0.1,
        help="1.0 = Text only, 0.0 = Image only"
    )
    
    st.divider()
    
    top_k_text = st.slider("Top K Text", 1, 20, config.DEFAULT_TOP_K_TEXT)
    top_k_images = st.slider("Top K Images", 1, 10, config.DEFAULT_TOP_K_IMAGES)
    top_k_evidence = st.slider("Top K Evidence (Ctx)", 1, 15, config.DEFAULT_TOP_K_EVIDENCE)

# Main Application Logic
def main():
    # Ensure data is loaded (this is cached in the class instance, so practically it runs once per restart)
    if "data_ingested" not in st.session_state:
        with st.spinner("Ingesting Data..."):
            rag.ingest_data()
            st.session_state["data_ingested"] = True
    
    query = st.text_input("Enter your query:", placeholder="e.g., What is the Transformer architecture?")
    
    if st.button("Search", type="primary"):
        if not query.strip():
            st.warning("Please enter a query.")
            return
        
        start_time = time.time()
        
        with st.spinner("Retrieving evidence..."):
            results = rag.retrieve(
                query=query, 
                top_k_text=top_k_text, 
                top_k_images=top_k_images, 
                top_k_evidence=top_k_evidence, 
                alpha=alpha, 
                method=retrieval_method
            )
            
            # Generate dummy answer (or connect LLM here)
            answer = rag.generate_answer(query, results)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Evaluate
        eval_metrics = rag.evaluate_results(query, results)
        
        # Log interaction
        evidence_ids = [r['id'] for r in results]
        log_interaction(query, retrieval_method, latency, evidence_ids, eval_metrics['p5'], eval_metrics['r10'])
        
        # Display Results
        st.subheader("Generated Answer")
        st.info(answer)
        
        st.subheader("Retrieval Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Latency", f"{latency:.3f}s")
        col2.metric("Evidence Count", len(results))
        col3.metric("Method", retrieval_method)
        col4.metric("P@5", f"{eval_metrics['p5']:.2f}")
        col5.metric("R@10", f"{eval_metrics['r10']:.2f}")
        
        st.divider()
        st.subheader("Evidence")
        
        # Separate Text and Image for cleaner display
        text_ev = [r for r in results if r['modality'] == 'text']
        img_ev = [r for r in results if r['modality'] == 'image']
        
        if img_ev:
            st.write("### Images")
            cols = st.columns(len(img_ev))
            for idx, item in enumerate(img_ev):
                with cols[idx]:
                    st.image(item['path'], caption=f"{item['id']} ({item['fused_score']:.3f})", use_container_width=True)
        
        if text_ev:
            st.write("### Text Segments")
            for item in text_ev:
                with st.expander(f"[{item['id']}] Score: {item['fused_score']:.3f}"):
                    st.write(item['content'])

if __name__ == "__main__":
    main()
