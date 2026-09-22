"""Multi-perspective recommendation and candidate aggregation."""

async def parallel_recommend(query, candidates, profile):
    results = await gather(
        run_perspective("price", query, candidates, profile),
        run_perspective("scenario", query, candidates, profile),
        run_perspective("quality", query, candidates, profile),
        run_perspective("diversity", query, candidates, profile),
    )
    merged = merge_candidate_scores(results)
    return rerank_with_business_constraints(merged, profile)


async def run_perspective(name, query, candidates, profile):
    return await agent_registry[name].run(
        query=query,
        candidates=candidates,
        profile=profile,
        memory=agent_memory.load(name, profile.user_id),
    )
