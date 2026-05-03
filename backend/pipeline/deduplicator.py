import numpy as np

_model = None
def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

SIMILARITY_DISCARD = 0.95
SIMILARITY_GROUP = 0.75
MAX_GROUP_SIZE = 5
COMPARISON_WINDOW = 200

def cosine_similarity(a, b):
    a = np.frombuffer(a, dtype=np.float32) if isinstance(a, bytes) else np.array(a)
    b = np.frombuffer(b, dtype=np.float32) if isinstance(b, bytes) else np.array(b)
    # prevent division by zero length if something went wrong
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

def process_article(conn, article: dict, embedding=None) -> str:
    # Phase 1 - exact duplicate check
    cursor = conn.execute("SELECT id FROM articles WHERE url_hash = ?", (article['url_hash'],))
    if cursor.fetchone():
        return "duplicate"

    # Phase 2 - semantic grouping using pre-computed embedding
    if embedding is None:
        return "new"

    try:
        cursor = conn.execute("""
            SELECT g.id, a.embedding, g.source_count
            FROM grouped_stories g
            JOIN articles a ON g.root_article_id = a.id
            ORDER BY g.created_at DESC
            LIMIT ?
        """, (COMPARISON_WINDOW,))

        groups = cursor.fetchall()
        best_match_id = None
        best_sim = -1

        for group in groups:
            group_id, root_emb_bytes, source_count = group
            if root_emb_bytes:
                sim = cosine_similarity(embedding, root_emb_bytes)
                if sim > SIMILARITY_DISCARD:
                    return "discarded"
                if sim >= SIMILARITY_GROUP and source_count < MAX_GROUP_SIZE:
                    if sim > best_sim:
                        best_sim = sim
                        best_match_id = group_id

        return str(best_match_id) if best_match_id else "new"

    except Exception as e:
        print(f"Embedding error: {e}")
        return "new"

def get_embedding_bytes(text):
    try:
        model = get_model()
        return model.encode(text).astype(np.float32).tobytes()
    except:
        return None
