# ChromaDB Vector Database Architecture: `15_DATA_AND_DATABASE/vector_database_explained.md`

[Back to Data Overview](data_directory_explained.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is the Vector Database?
The vector database is the dense semantic retrieval store located in `data/chroma_db/`. It is powered by **ChromaDB** (`PersistentClient`), an open-source, embedded vector database optimized for AI search applications.

### Core Statistics:
- **Persistence Directory**: `data/chroma_db/`
- **Underlying Database Engine**: Embedded SQLite (`chroma.sqlite3`) + C++ HNSW binary index.
- **Indexed Child Passages**: **7,470 passages**.
- **Dense Embedding Model**: `BAAI/bge-m3` (1024 dimensions) or `all-MiniLM-L6-v2` (384 dimensions).
- **Search Latency**: ~35 to 55 milliseconds for top-30 ANN vector retrieval.

---

## 2. ChromaDB Internal Architecture

ChromaDB uses a hybrid two-tier storage model:

```
data/chroma_db/
├── chroma.sqlite3            # SQLite relational database
│   ├── collections           # Stores collection names, metadata, and dimensions
│   ├── embeddings            # Stores document text, unique chunk IDs, and JSON metadata
│   └── segments              # Index segment allocation table
│
└── <uuid>/                   # Binary HNSW Vector Index Segment
    ├── data_level0.bin       # Base level of Hierarchical Navigable Small World graph
    ├── header.bin            # Graph header (entry point node, number of layers)
    ├── length.bin            # Vector dimensionality specifications
    └── link_lists.bin        # Neighbor adjacency lists for fast graph navigation
```

---

## 3. Dual Collections & The Dimension Guard

ChromaDB strictly prohibits mixing vector embeddings of differing dimensions in the same collection. To allow experimentation between lightweight and large embedding models, the system maintains **two isolated collections**:

| Collection Name | Embedding Model | Vector Dimension | Purpose |
| :--- | :--- | :--- | :--- |
| **`indian_legal_rag_bgem3`** | `BAAI/bge-m3` | **1024 dimensions** | Production high-accuracy multi-lingual legal retrieval. |
| **`indian_legal_rag`** | `all-MiniLM-L6-v2` | **384 dimensions** | Lightweight, high-speed baseline evaluation. |

### Dimension Validation Guard (`config.py`):
```python
def validate_embedding_dimensions(model_name: str, embedding_vector: List[float]) -> bool:
    """Guarantees embedding dimensions match collection specifications before querying."""
    expected_dim = BGE_M3_EMBEDDING_DIM if "bge-m3" in model_name.lower() else MINILM_EMBEDDING_DIM
    if len(embedding_vector) != expected_dim:
        raise ValueError(
            f"Embedding Dimension Mismatch! Model '{model_name}' expected {expected_dim}-d "
            f"but received {len(embedding_vector)}-d vector."
        )
    return True
```

---

## 4. The HNSW Graph Index Algorithm

ChromaDB indexes vectors using **Hierarchical Navigable Small World (HNSW)** graphs, the state-of-the-art algorithm for Approximate Nearest Neighbor (ANN) search:

```
Layer 2 (Sparse, Long-range hops)     Node A ────────────────────────> Node Z
                                        │                                │
Layer 1 (Medium density)              Node A ──────────> Node M ───────> Node Z
                                        │                  │             │
Layer 0 (Dense, All 7,470 vectors)    Node A ──> Node B ─> Node M ─────> Node Z
```

### How HNSW Operates:
1. **Hierarchical Multi-Layer Graph**: Top layers contain few nodes with long-range links (like express highways); bottom layers contain all nodes with local links (local streets).
2. **Logarithmic Search Complexity**: Search begins at Layer 2, making greedy long-range hops toward the query vector. Once a local minimum is reached, search descends to Layer 1, and finally Layer 0.
3. **Speed**: Finds the 30 closest vectors out of 7,470 passages in $O(\log N)$ time ($\approx 40$ milliseconds), compared to $O(N)$ brute-force search which would require computing dot products across all 7,470 vectors.

---

## 5. Mathematical Distance Conversion

ChromaDB computes **Cosine Distance** $d \in [0, 2]$:
$$d(\vec{q}, \vec{p}) = 1 - \frac{\vec{q} \cdot \vec{p}}{\|\vec{q}\|_2 \|\vec{p}\|_2}$$
- Identical vectors $\to d = 0.0$.
- Orthogonal vectors $\to d = 1.0$.
- Diametrically opposite vectors $\to d = 2.0$.

### Similarity Inversion in `DenseRetriever` (`retrieval/dense_retrieval.py`):
Information retrieval rankings require scores where **higher is better**. `DenseRetriever` converts distance into similarity:
$$s = 1.0 - d = \frac{\vec{q} \cdot \vec{p}}{\|\vec{q}\|_2 \|\vec{p}\|_2}$$
Candidates are sorted descending by $s$.

---

## 6. Viva Presentation & Defense Q&A

### Q1: Why did you choose ChromaDB over cloud vector databases like Pinecone or Weaviate?
> **Student Answer**:
> *"ChromaDB is completely embedded and self-contained. It stores all vectors and metadata locally in `data/chroma_db/` without requiring external cloud accounts, network calls, or monthly subscription fees. This guarantees complete data sovereignty (vital for sensitive legal workflows), eliminates cloud latency, and allows the entire project to run 100% offline during classroom demonstrations."*

### Q2: What is an HNSW graph and why is it faster than brute-force cosine search?
> **Student Answer**:
> *"HNSW stands for Hierarchical Navigable Small World graph. A brute-force linear search must compute 1024-dimensional dot products against every single one of the 7,470 vectors ($O(N)$ complexity). HNSW constructs a multi-layer graph with skip-list properties: top layers make rapid long-range hops across vector space, and bottom layers refine the local search. This reduces query search complexity to $O(\log N)$, retrieving top candidates in under 45 milliseconds on standard CPU."*

