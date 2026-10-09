"""
Hybrid Retriever Module with Reciprocal Rank Fusion (RRF) and Legal Named Entity Recognition (NER).
Maintains backward compatibility for legacy callers and tests while delegating to the modular
components in the retrieval/ package (BM25Retriever, DenseRetriever, fuse, apply_entity_boost,
CrossEncoderReranker, and HybridRetriever).
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    RRF_K,
    DEFAULT_TOP_K,
    ENTITY_BOOST_WEIGHT,
    FINAL_TOP_K,
    PARENT_STORE_PATH,
)
from ingestion import ParentChildIngestor, simple_tokenize
from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.rrf import fuse
from retrieval.entity_boost import apply_entity_boost
from retrieval.reranker import CrossEncoderReranker
from retrieval.hybrid_retriever import HybridRetriever


class LegalNERExtractor:
    """
    Named Entity Recognition (NER) Extractor tailored for Indian Constitutional Law.
    Extracts Article numbers, Landmark Case names, Fundamental Rights, and Legal concepts.
    Maintained for direct backward compatibility with legacy tests and app callers.
    """

    ARTICLE_PATTERN = re.compile(
        r'\b(?:Article|Art\.?|Art)\s*(\d+[A-Z]?|Preamble)\b', re.IGNORECASE
    )

    KNOWN_CASES = [
        "Kesavananda Bharati", "Kesavananda", "Maneka Gandhi", "Maneka",
        "Puttaswamy", "Minerva Mills", "S.R. Bommai", "Bommai",
        "A.K. Gopalan", "Gopalan", "Royappa", "Unni Krishnan"
    ]

    LEGAL_CONCEPTS = [
        "basic structure", "right to privacy", "privacy", "freedom of speech",
        "equality before law", "due process", "equal protection",
        "habeas corpus", "mandamus", "writs", "secularism", "federalism",
        "fundamental rights", "fundamental duties", "amendment", "abrogation"
    ]

    @classmethod
    def extract_entities(cls, query: str) -> Dict[str, List[str]]:
        """Extract legal entities from user query."""
        entities = {
            "articles": [],
            "cases": [],
            "concepts": []
        }

        if not query:
            return entities

        # 1. Extract Articles
        articles = cls.ARTICLE_PATTERN.findall(query)
        for art in articles:
            if art.lower() == "preamble":
                entities["articles"].append("Preamble")
            else:
                entities["articles"].append(f"Article {art.upper()}")

        if "preamble" in query.lower() and "Preamble" not in entities["articles"]:
            entities["articles"].append("Preamble")

        # 2. Extract Case Names
        query_lower = query.lower()
        for case in cls.KNOWN_CASES:
            if case.lower() in query_lower:
                entities["cases"].append(case)

        # 3. Extract Legal Concepts
        for concept in cls.LEGAL_CONCEPTS:
            if concept in query_lower:
                entities["concepts"].append(concept)

        return entities


class HybridRRFRetriever:
    """
    Advanced Hybrid Search Engine combining BM25 (Sparse) and Vector Embeddings (Dense)
    using Reciprocal Rank Fusion (RRF), enhanced with Legal NER context boosting.
    Delegates to modular retrieval package components while preserving exact legacy signatures.
    """

    def __init__(self, ingestor: Optional[ParentChildIngestor] = None):
        if ingestor is None:
            ingestor = ParentChildIngestor()
            ingestor.process_parent_child_chunks()
            ingestor.build_vector_store()
            ingestor.build_bm25_index()

        self.parent_store = ingestor.parent_store
        self.child_chunks = ingestor.child_chunks
        self.bm25_index = ingestor.bm25_index

        # Connect to persistent ChromaDB collection
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=DEFAULT_EMBEDDING_MODEL
        )
        self.collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_fn
        )

        # Map child_id to child dict for fast lookup
        self.child_dict = {c["child_id"]: c for c in self.child_chunks if "child_id" in c}

        # Sub-component instances
        self.bm25_retriever = BM25Retriever(
            bm25_index=self.bm25_index,
            child_chunks=self.child_chunks,
            parent_store=self.parent_store,
        )
        self.dense_retriever = DenseRetriever(
            collection=self.collection,
            parent_store=self.parent_store,
            child_chunks=self.child_chunks,
        )
        self._hybrid_retriever = HybridRetriever(
            bm25_retriever=self.bm25_retriever,
            dense_retriever=self.dense_retriever,
            parent_store=self.parent_store,
            use_reranker=False,  # Legacy retrieve() default runs BM25+Dense+RRF+EntityBoost
        )

    def sparse_search_bm25(self, query: str, top_k: int = 10) -> List[Tuple[str, float, int]]:
        """Perform BM25 sparse keyword search and return (child_id, score, rank)."""
        tokens = simple_tokenize(query)
        if not tokens or self.bm25_index is None:
            return []
        scores = self.bm25_index.get_scores(tokens)

        # Rank indices descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            if scores[idx] > 0:
                child_id = self.child_chunks[idx]["child_id"]
                results.append((child_id, float(scores[idx]), rank))

        return results

    def dense_search_vector(self, query: str, top_k: int = 10) -> List[Tuple[str, float, int]]:
        """Perform dense vector embedding similarity search and return (child_id, distance, rank)."""
        if not query or self.collection is None or self.collection.count() == 0:
            return []

        query_results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )

        results = []
        if query_results and "ids" in query_results and query_results["ids"]:
            ids = query_results["ids"][0]
            distances = query_results["distances"][0] if "distances" in query_results else [0.0] * len(ids)

            for rank, (child_id, dist) in enumerate(zip(ids, distances), start=1):
                results.append((child_id, float(dist), rank))

        return results

    def reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[str, float, int]],
        vector_results: List[Tuple[str, float, int]],
        ner_entities: Dict[str, List[str]],
        k_constant: int = RRF_K
    ) -> List[Dict[str, Any]]:
        """
        Combine BM25 and Vector ranks using Reciprocal Rank Fusion (RRF).
        Apply RRF score = sum(1 / (k + rank)) + optional entity boost.
        Maintains backward compatibility with legacy test assertions.
        """
        rrf_scores: Dict[str, float] = {}
        child_rank_details: Dict[str, Dict[str, int]] = {}

        # 1. Add BM25 scores
        for child_id, score, rank in bm25_results:
            rrf_scores[child_id] = rrf_scores.get(child_id, 0.0) + (1.0 / (k_constant + rank))
            if child_id not in child_rank_details:
                child_rank_details[child_id] = {}
            child_rank_details[child_id]["bm25_rank"] = rank

        # 2. Add Vector scores
        for child_id, dist, rank in vector_results:
            rrf_scores[child_id] = rrf_scores.get(child_id, 0.0) + (1.0 / (k_constant + rank))
            if child_id not in child_rank_details:
                child_rank_details[child_id] = {}
            child_rank_details[child_id]["vector_rank"] = rank

        # 3. Apply Legal NER context boost
        for child_id in rrf_scores:
            child = self.child_dict.get(child_id, {})
            # Boost if article matches
            art_num = child.get("article_number", "")
            for ent_art in ner_entities.get("articles", []):
                if ent_art.lower() in art_num.lower() or art_num.lower() in ent_art.lower():
                    rrf_scores[child_id] += 0.05

            # Boost if case matches
            c_name = child.get("case_name", "")
            for ent_case in ner_entities.get("cases", []):
                if ent_case.lower() in c_name.lower():
                    rrf_scores[child_id] += 0.05

        # Sort by final RRF score descending
        sorted_children = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

        fused_results = []
        for rank_idx, (child_id, final_score) in enumerate(sorted_children, start=1):
            child_data = self.child_dict.get(child_id, {})
            parent_id = child_data.get("parent_id", "")
            parent_data = self.parent_store.get(parent_id, {})

            ranks = child_rank_details.get(child_id, {})
            meta = {
                "parent_id": parent_id,
                "article_number": child_data.get("article_number", ""),
                "case_name": child_data.get("case_name", ""),
                "title": child_data.get("title", ""),
                "parent_data": parent_data,
            }

            fused_results.append({
                # Standardized Schema
                "document_id": parent_id,
                "chunk_id": child_id,
                "score": round(final_score, 5),
                "rank": rank_idx,
                "text": child_data.get("text", ""),
                "doc_type": child_data.get("doc_type", ""),
                "metadata": meta,
                # Backward-compatibility fields
                "child_id": child_id,
                "child_text": child_data.get("text", ""),
                "parent_id": parent_id,
                "parent_data": parent_data,
                "rrf_score": round(final_score, 5),
                "bm25_rank": ranks.get("bm25_rank", "N/A"),
                "vector_rank": ranks.get("vector_rank", "N/A"),
            })

        return fused_results

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Execute full hybrid retrieval pipeline:
        1. Extract Legal NER entities
        2. Sparse BM25 search
        3. Dense Vector search
        4. RRF fusion + entity boosting
        5. Return structured results with child passages & parent contexts
        """
        # Step 1: Legal NER Extraction
        entities = LegalNERExtractor.extract_entities(query)

        # Step 2 & 3: Sparse + Dense Searches
        bm25_res = self.sparse_search_bm25(query, top_k=top_k * 3)
        vector_res = self.dense_search_vector(query, top_k=top_k * 3)

        # Step 4: RRF Fusion
        fused_results = self.reciprocal_rank_fusion(
            bm25_res, vector_res, entities, k_constant=RRF_K
        )

        top_results = fused_results[:top_k]

        return {
            "query": query,
            "entities": entities,
            "results": top_results
        }


__all__ = [
    "LegalNERExtractor",
    "HybridRRFRetriever",
    "BM25Retriever",
    "DenseRetriever",
    "CrossEncoderReranker",
    "HybridRetriever",
    "fuse",
    "apply_entity_boost",
]


if __name__ == "__main__":
    retriever = HybridRRFRetriever()
    sample_q = "What did Supreme Court rule regarding Right to Privacy in Puttaswamy under Article 21?"
    output = retriever.retrieve(sample_q, top_k=3)
    print("\n--- QUERY ENTITIES ---")
    print(output["entities"])
    print(f"\n--- RETRIEVED TOP {len(output['results'])} RESULTS ---")
    for res in output["results"]:
        print(f"Child ID: {res['child_id']} | RRF Score: {res['rrf_score']} | BM25 Rank: {res['bm25_rank']} | Vector Rank: {res['vector_rank']}")
        print(f"Snippet: {res['child_text'][:120]}...\n")
