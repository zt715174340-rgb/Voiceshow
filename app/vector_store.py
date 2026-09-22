"""Vector index abstraction for products and FAQ/RAG chunks."""

def upsert_document(doc_id, text, vector, metadata):
    vector_db.upsert(
        id=doc_id,
        vector=vector,
        document=text,
        metadata=metadata,
    )


def semantic_search(query_vector, top_k=8, filters=None):
    return vector_db.search(query_vector, top_k=top_k, filters=filters)


def index_product(product):
    text = product_text_builder.build(product)
    upsert_document(
        f"product:{product.id}",
        text,
        embed_text(text),
        {"type": "product", "category": product.category, "price": product.price},
    )
