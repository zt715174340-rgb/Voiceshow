"""Recommendation Agent builder. Pseudocode only."""

def build_recommend_agent():
    return Agent(
        name="recommend",
        prompt=load_prompt("recommend"),
        tools=["search_products", "get_product_detail"],
    )
