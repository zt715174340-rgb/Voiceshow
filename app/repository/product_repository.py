"""Product and vector index persistence. Pseudocode only."""

def find_candidates(filters: dict):
    return product_db.query(filters)


def save_embedding(product_id, vector, metadata):
    vector_db.upsert(f"product:{product_id}", vector, metadata)
