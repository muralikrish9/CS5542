import os
import re
import glob
import requests
import fitz  # PyMuPDF
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# Try importing specialized libraries, handle gracefully if missing (though they should be installed)
try:
    from sentence_transformers import SentenceTransformer, util, CrossEncoder
    HAS_DENSE = True
except Exception as e:
    print(f"Dense retrieval disabled due to import error: {e}")
    HAS_DENSE = False

import config

@dataclass
class TextChunk:
    chunk_id: str
    doc_id: str
    page_num: int
    text: str

@dataclass
class ImageItem:
    item_id: str
    path: str
    caption: str

class RAGEngine:
    def __init__(self):
        self.text_chunks: List[TextChunk] = []
        self.image_items: List[ImageItem] = []
        
        # Retrieval Indices
        self.text_vec = None
        self.text_X = None
        self.img_vec = None
        self.img_X = None
        
        # Models
        self.dense_model = None
        self.dense_embeddings = None
        self.reranker_model = None
        
        self._load_models()
        
    def _load_models(self):
        if HAS_DENSE:
            # We delay loading these slightly until needed or load them now.
            # For a persistent app, loading on init is fine.
            # To speed up startup, we could lazy load.
            pass

    def check_and_download_data(self):
        """Ensures PDFs and Images exist."""
        os.makedirs(config.PDF_DIR, exist_ok=True)
        os.makedirs(config.IMG_DIR, exist_ok=True)

        # Papers to download if directory is empty
        papers = {
            "attention.pdf": "https://arxiv.org/pdf/1706.03762.pdf",
            "bert.pdf": "https://arxiv.org/pdf/1810.04805.pdf"
        }
        
        # Check if we have PDFs
        existing_pdfs = glob.glob(os.path.join(config.PDF_DIR, "*.pdf"))
        if not existing_pdfs:
            print("Downloading default papers...")
            for name, url in papers.items():
                path = os.path.join(config.PDF_DIR, name)
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(url, headers=headers)
                    if resp.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(resp.content)
                except Exception as e:
                    print(f"Failed to download {name}: {e}")
        
        # Check if we have images
        # We need to extract them if they don't exist
        existing_imgs = glob.glob(os.path.join(config.IMG_DIR, "*.*"))
        if len(existing_imgs) < 2:
            print("Extracting images from PDFs...")
            for p in glob.glob(os.path.join(config.PDF_DIR, "*.pdf")):
                self._extract_images_from_pdf(p, config.IMG_DIR)

    def _extract_images_from_pdf(self, pdf_path: str, output_dir: str):
        doc = fitz.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    if len(image_bytes) < 3000: continue # Skip tiny images
                    
                    fname = f"{base_name}_p{i+1}_{img_index+1}.{image_ext}"
                    out_path = os.path.join(output_dir, fname)
                    with open(out_path, "wb") as f:
                        f.write(image_bytes)
                except Exception as e:
                    pass

    def ingest_data(self):
        """Loads PDFs and Images, chunks text, builds indexes."""
        self.check_and_download_data()
        
        # 1. Load Text
        pdfs = sorted(glob.glob(os.path.join(config.PDF_DIR, "*.pdf")))
        raw_chunks = []
        for p in pdfs:
            raw_chunks.extend(self._extract_pdf_pages(p))
            
        if config.CHUNKING_MODE == "fixed":
            self.text_chunks = self._chunk_text_fixed(raw_chunks)
        else:
            self.text_chunks = raw_chunks
            
        # 2. Load Images
        self.image_items = []
        for p in sorted(glob.glob(os.path.join(config.IMG_DIR, "*.*"))):
            base = os.path.basename(p)
            caption = os.path.splitext(base)[0].replace("_", " ")
            self.image_items.append(ImageItem(item_id=base, path=p, caption=caption))
            
        # 3. Build TF-IDF Indices
        self._build_tfidf()
        
        # 4. Build Dense Index (if enabled)
        if HAS_DENSE:
            print("Loading Dense Models...")
            self.dense_model = SentenceTransformer(config.DENSE_MODEL_NAME)
            corpus_text = [c.text for c in self.text_chunks]
            self.dense_embeddings = self.dense_model.encode(corpus_text, convert_to_tensor=True)
            
            try:
                self.reranker_model = CrossEncoder(config.RERANK_MODEL_NAME)
            except Exception as e:
                print(f"Reranker load failed: {e}")
                
        print(f"Ingestion Complete. Text Chunks: {len(self.text_chunks)}, Images: {len(self.image_items)}")

    def _extract_pdf_pages(self, pdf_path: str) -> List[TextChunk]:
        doc_id = os.path.basename(pdf_path)
        doc = fitz.open(pdf_path)
        out: List[TextChunk] = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = self._clean_text(page.get_text("text"))
            if text:
                out.append(TextChunk(
                    chunk_id=f"{doc_id}::p{i+1}",
                    doc_id=doc_id,
                    page_num=i+1,
                    text=text
                ))
        return out

    def _clean_text(self, s: str) -> str:
        s = s or ""
        s = re.sub(r"\\s+", " ", s).strip()
        return s

    def _chunk_text_fixed(self, text_chunks: List[TextChunk]) -> List[TextChunk]:
        chunk_size = config.CHUNK_SIZE
        chunk_overlap = config.CHUNK_OVERLAP
        new_chunks = []
        for ch in text_chunks:
            text = ch.text
            if len(text) <= chunk_size:
                new_chunks.append(ch)
                continue
                
            start = 0
            sub_idx = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                sub_text = text[start:end]
                new_chunks.append(TextChunk(
                    chunk_id=f"{ch.chunk_id}::sub{sub_idx}",
                    doc_id=ch.doc_id,
                    page_num=ch.page_num,
                    text=sub_text
                ))
                if end == len(text): break
                start += (chunk_size - chunk_overlap)
                sub_idx += 1
        return new_chunks

    def _build_tfidf(self):
        # Text Index
        corpus_t = [c.text for c in self.text_chunks]
        self.text_vec = TfidfVectorizer(lowercase=True, stop_words="english")
        self.text_X = self.text_vec.fit_transform(corpus_t)
        self.text_X = normalize(self.text_X)
        
        # Image Index
        corpus_i = [it.caption for it in self.image_items]
        self.img_vec = TfidfVectorizer(lowercase=True, stop_words="english")
        self.img_X = self.img_vec.fit_transform(corpus_i)
        self.img_X = normalize(self.img_X)

    def _tfidf_retrieve(self, query: str, vec, X, top_k: int):
        q = vec.transform([query])
        q = normalize(q)
        scores = (X @ q.T).toarray().ravel()
        idx = np.argsort(-scores)[:top_k]
        return [(int(i), float(scores[i])) for i in idx]

    def _dense_retrieve(self, query: str, top_k: int):
        if self.dense_model is None: return []
        query_emb = self.dense_model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_emb, self.dense_embeddings, top_k=top_k)[0]
        return [(h['corpus_id'], h['score']) for h in hits]

    def _rerank_hits(self, query: str, hit_list: List[Tuple[int, float]], top_k: int):
        if self.reranker_model is None or not hit_list:
            return hit_list[:top_k]
        
        pairs = [[query, self.text_chunks[idx].text] for idx, score in hit_list]
        scores = self.reranker_model.predict(pairs)
        ranked = sorted(list(zip(hit_list, scores)), key=lambda x: x[1], reverse=True)
        return [(item[0][0], float(item[1])) for item in ranked[:top_k]]

    def _normalize_scores(self, pairs):
        if not pairs: return []
        scores = [s for _, s in pairs]
        lo, hi = min(scores), max(scores)
        if abs(hi - lo) < 1e-12: return [(i, 1.0) for i, _ in pairs]
        return [(i, (s - lo) / (hi - lo)) for i, s in pairs]

    def retrieve(self, query: str, top_k_text: int, top_k_images: int, top_k_evidence: int, alpha: float, method: str):
        # 1. Text Retrieval
        text_hits = []
        
        # Sparse Retrieval
        if method in ["sparse", "hybrid", "rerank"]:
            text_hits = self._tfidf_retrieve(query, self.text_vec, self.text_X, top_k=top_k_text * 2)

        # Dense Retrieval
        dense_hits = []
        if method in ["dense", "hybrid", "rerank"] and HAS_DENSE:
            dense_hits = self._dense_retrieve(query, top_k=top_k_text * 2)

        # Combine
        final_text_hits = []
        if method == "sparse":
            final_text_hits = text_hits
        elif method == "dense":
            final_text_hits = dense_hits
        elif method == "hybrid":
            combined = {}
            s_norm = self._normalize_scores(text_hits)
            d_norm = self._normalize_scores(dense_hits)
            for idx, sc in s_norm: combined[idx] = combined.get(idx, 0) + (0.5 * sc)
            for idx, sc in d_norm: combined[idx] = combined.get(idx, 0) + (0.5 * sc)
            final_text_hits = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        elif method == "rerank":
            pool_indices = set([i for i,s in text_hits] + [i for i,s in dense_hits])
            candidates = [(i, 0.0) for i in pool_indices]
            final_text_hits = self._rerank_hits(query, candidates, top_k=top_k_text)
            
        final_text_hits = final_text_hits[:top_k_text]
        
        # 2. Image Retrieval
        img_hits = self._tfidf_retrieve(query, self.img_vec, self.img_X, top_k=top_k_images)
        
        # 3. Fusion
        text_norm = self._normalize_scores(final_text_hits)
        img_norm = self._normalize_scores(img_hits)
        
        fused = []
        for idx, s in text_norm:
            ch = self.text_chunks[idx]
            fused.append({
                "modality": "text",
                "id": ch.chunk_id,
                "fused_score": alpha * s,
                "content": ch.text,
                "path": None
            })
            
        for idx, s in img_norm:
            it = self.image_items[idx]
            fused.append({
                "modality": "image",
                "id": it.item_id,
                "fused_score": (1.0 - alpha) * s,
                "content": it.caption,
                "path": it.path
            })
            
        fused = sorted(fused, key=lambda d: d["fused_score"], reverse=True)[:top_k_evidence]
        return fused

    def generate_answer(self, query: str, evidence: List[Dict[str, Any]]):
        lines = []
        for ev in evidence:
            if ev["modality"] == "text":
                lines.append(f"[TEXT] {ev['content'][:200]}...")
            else:
                lines.append(f"[IMAGE] {ev['content']}")
        
        context_str = "\n".join(lines)
        if not lines:
            return "I don't have enough information to answer that."
            
        return f"Based on the retrieved evidence:\n{context_str}\n\n(Note: This is an extractive baseline. Connect an LLM to generate fluent answers.)"

    def evaluate_results(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates P@5 and R@10 if query matches a known ground truth."""
        # Normalize query for matching
        q_norm = query.strip().lower()
        matched_rubric = None
        
        # Check against predefined queries
        for q_item in QUERIES:
            if q_norm == q_item["question"].lower() or q_norm in q_item["question"].lower():
                matched_rubric = q_item["rubric"]
                break
        
        if not matched_rubric:
            return {"p5": -1.0, "r10": -1.0}
            
        must_have = [w.lower() for w in matched_rubric["must_have_keywords"]]
        
        # Calculate Precision@5
        # "Relevant" if content contains at least one must_have keyword
        relevant_count_5 = 0
        for i, r in enumerate(results[:5]):
            content = r["content"].lower()
            if any(w in content for w in must_have):
                relevant_count_5 += 1
        p5 = relevant_count_5 / 5.0 if results else 0.0
        
        # Calculate Recall@10 (Approximation based on retrieved window)
        # In a real system, R@10 = (rel_in_top10) / (total_rel_in_corpus).
        # We don't know total_rel in corpus easily without full scan.
        # But for this lab we often approximate or just report "Hit Rate" logic or assumption.
        # Let's assume total_relevant is at least 1 (if we find any).
        # Or let's just count relevant in top 10.
        relevant_count_10 = 0
        for i, r in enumerate(results[:10]):
            content = r["content"].lower()
            if any(w in content for w in must_have):
                relevant_count_10 += 1
        
        # If we assume there are roughly 5 relevant chunks per query in the doc on average?
        # Let's just return the raw count for recall-proxy or normalize by a fixed assumed relevant count (e.g. 5)
        # For the notebook logic, often R@10 is just "did we find relevant stuff?"
        # Let's normalize by min(10, total_found_in_top_10 + 1) to avoid div/0, or just return relevant_count_10 for now?
        # Better: let's treat "Recall" as "Hit Rate" (did we find ANY relevant?) or 
        # just normalize by a constant like 3 (assuming 3 golden chunks exist).
        ASSUMED_TOTAL_RELEVANT = 3.0
        r10 = min(relevant_count_10 / ASSUMED_TOTAL_RELEVANT, 1.0)
        
        return {"p5": p5, "r10": r10}

# Predefined Queries and Rubrics for Evaluation
QUERIES = [
    {
        "id": "Q1",
        "question": "What is the Transformer architecture and how does it differ from RNNs/CNNs?",
        "rubric": {
            "must_have_keywords": ["transformer", "architecture", "recurrence", "convolution"],
            "optional_keywords": ["attention", "sequential", "parallel"]
        }
    },
    {
        "id": "Q2",
        "question": "How does BERT use the Transformer encoder?",
        "rubric": {
            "must_have_keywords": ["bert", "encoder", "bidirectional", "transformer"],
            "optional_keywords": ["masked", "lm", "pre-training"]
        }
    },
    {
        "id": "Q3",
        "question": "Describe the difference between the 'base' and 'large' models.",
        "rubric": {
            "must_have_keywords": ["base", "large", "parameter", "layer"],
            "optional_keywords": ["dimension", "head", "performance"]
        }
    },
]

# Singleton instance for simple import
rag = RAGEngine()
