# VoiceShop 与原始 jc-voice-shopping 的差距及伪代码

> 除“当前已具备”部分外，本文均为设计草案，不代表已经接入运行链路。

## 1. 当前 Demo 已具备

| 能力 | 状态 |
| --- | --- |
| Web 服务与前端 | 已实现，FastAPI/HTTP + web |
| 多轮会话 | 简化实现，session_id、消息落库、最近消息 |
| 意图识别 | 简化实现，DeepSeek 判断主意图，规则提取槽位 |
| 商品检索 | JSON 商品 + 结构化筛选 |
| RAG | 轻量实现，Markdown + TF-IDF，不是真实 Embedding |
| FAQ | 基础查询已具备 |
| 数据持久化 | SQLite 保存会话、消息、订单、行为、FAQ、Trace |
| 浏览器语音 | 基础 ASR/TTS，不是服务端流式语音 |
| 评测 | 基础槽位 F1、Recall@5、澄清准确率 |

## 2. 与原始 VoiceShop 的主要差距

当前目录不是少几个文件，而是少了以下工程能力：

1. 认证、安全、记忆、订单、推荐、语音和向量服务边界。
2. Redis 短期记忆、意图缓存、会话状态和待确认订单。
3. Embedding + pgvector 的商品和 FAQ 语义检索。
4. WebSocket ASR/TTS 流式链路。
5. 意图、情绪、推荐视角、合规等 Agent 或服务拆分。
6. 完整订单状态、用户画像、行为沉淀、Trace 和回归评测。

原项目模块大致为：

~~~text
agent, compliance, config, controller, dto, entity, event, listener,
memory, repository, security, service, voice
~~~

当前 Demo 是：

~~~text
FastAPI -> graph -> llm/tools/rag/db
             |
          SQLite + JSON + 本地 TF-IDF
~~~

## 3. 模块映射

| 原项目 | Python 目标 | 当前状态 |
| --- | --- | --- |
| IntentService | app/intent.py | 逻辑在 graph.py/llm.py |
| OrchestratorService | app/graph.py | 已有简化实现 |
| ClarifyRuleService | app/clarify.py | 基础澄清 |
| ProductVectorService | app/vector_store.py | 缺失 |
| FaqVectorService | app/rag.py | TF-IDF 简化 |
| EmbeddingService | app/embedding.py | 缺失 |
| ProfileReranker | app/profile.py | 画像未参与排序 |
| ParallelRecommendService | app/recommend.py | 并行评分模拟 |
| OrderService | app/orders.py | 基础订单接口 |
| ShortTermMemory | app/memory.py | SQLite 替代 |
| IntentCache | app/cache.py | 缺失 Redis |
| EmotionService | app/emotion.py | 缺失 |
| ComplianceService | app/compliance.py | 扩展点 |
| Auth/Security | app/auth.py | 缺失真实认证 |
| WebSocket ASR/TTS | app/voice_ws.py | 缺失 |
| Trace/Metrics/Event | app/observability.py | 基础 Trace |

## 4. 统一数据结构

~~~python
class IntentResult:
    intent: str
    confidence: float
    slots: dict
    missing_slots: list[str]
    source: str                 # model / rule / fallback


class ToolResult:
    ok: bool
    data: object
    error_code: str | None
    trace_id: str


class SessionState:
    session_id: str
    user_id: int
    phase: str                  # collecting / recommending / confirming
    intent: str | None
    slots: dict
    excluded_constraints: list[str]
    last_product_ids: list[int]
    pending_order_id: str | None
~~~

## 5. 认证和权限伪代码

当前 Demo 的 user_id 仍是演示值。原项目要求登录后从 Token 取得当前用户，并校验资源归属。

~~~python
def register(email, password):
    validate_email(email)
    validate_password_strength(password)
    if user_repo.exists(email):
        raise BusinessError("EMAIL_EXISTS")
    user = user_repo.create(
        email=email,
        password_hash=password_hasher.hash(password),
        status="active",
    )
    return issue_access_token(user.id)


def login(email, password):
    user = user_repo.find_by_email(email)
    if not user or not password_hasher.verify(password, user.password_hash):
        raise AuthError("INVALID_CREDENTIALS")
    return issue_access_token(user.id)


def get_current_user(access_token):
    payload = jwt.verify(access_token, settings.jwt_secret)
    return user_repo.get(payload["user_id"])


def require_permission(user, permission):
    if permission not in user.permissions:
        raise PermissionError(permission)
~~~

## 6. 多轮会话和记忆隔离

~~~python
MEMORY_POLICY = {
    "intent": {"max_turns": 3, "ttl_seconds": 300},
    "recommend": {"max_turns": 8, "ttl_seconds": 1800},
    "emotion": {"max_turns": 40, "ttl_seconds": 1800},
}


def append_turn(session_id, role, content, metadata=None):
    redis.rpush(
        f"session:{session_id}:messages",
        serialize(role, content, metadata),
    )
    redis.expire(f"session:{session_id}:messages", 1800)


def recent_turns(session_id, agent_name):
    policy = MEMORY_POLICY[agent_name]
    raw = redis.lrange(
        f"session:{session_id}:messages",
        -policy["max_turns"],
        -1,
    )
    return [deserialize(item) for item in raw]


def summarize_old_history(session_id):
    old_turns = load_old_turns(session_id)
    save_memory_summary(session_id, summarizer(old_turns))
~~~

## 7. Intent Agent：模型判断，规则抽取和校验

正确流程：

~~~text
历史上下文 -> 模型判断主意图 -> 规则/Schema 抽取槽位
-> 上下文修正 -> 业务校验 -> 工具或澄清
~~~

~~~python
ALLOWED_INTENTS = {
    "product_recommendation", "product_compare",
    "product_price_query", "product_availability_query",
    "product_detail_query", "order_history_query",
    "order_detail_query", "logistics_query",
    "after_sales_query", "knowledge_query",
    "change_preference", "chitchat", "greeting", "unknown",
}


def classify_intent(session_id, query):
    cached = intent_cache.get(session_id, fingerprint(query))
    if cached:
        return cached

    history = recent_turns(session_id, "intent")
    raw = llm.json_call(
        system=INTENT_PROMPT,
        input={"history": history, "query": query, "allowed": ALLOWED_INTENTS},
    )

    result = parse_and_validate_intent(raw)
    if result is None:
        result = IntentResult(
            intent="unknown",
            confidence=0.0,
            slots=extract_slots_by_rule(query),
            source="fallback",
        )

    result.slots = merge_rule_slots(
        result.slots,
        extract_slots_by_rule(query),
    )
    result = revise_intent_by_context(result, history)

    if result.confidence >= 0.65:
        intent_cache.set(session_id, fingerprint(query), result, ttl=300)
    return result


def revise_intent_by_context(result, history):
    last = last_recommendation(history)

    # “有什么价位”在推荐上下文中应当是价格查询。
    if last and contains_price_question(result.slots, history):
        result.intent = "product_price_query"

    # 只有明确否定或排除时，才是修改偏好。
    if explicit_negation(result.slots) and last:
        result.intent = "change_preference"

    return result
~~~

## 8. LangGraph 编排伪代码

~~~python
def build_graph():
    graph = StateGraph(VoiceShopState)

    for name, handler in {
        "load_session": load_session,
        "compliance_input": check_input_compliance,
        "classify_intent": classify_intent_node,
        "extract_slots": extract_slots_node,
        "validate_slots": validate_slots_node,
        "clarify": clarify_node,
        "retrieve_products": retrieve_products_node,
        "retrieve_knowledge": retrieve_knowledge_node,
        "query_orders": query_orders_node,
        "recommend": recommend_node,
        "generate_answer": generate_answer_node,
        "compliance_output": check_output_compliance,
        "persist_memory": persist_memory_node,
        "write_trace": write_trace_node,
    }.items():
        graph.add_node(name, handler)

    graph.add_edge(START, "load_session")
    graph.add_edge("load_session", "compliance_input")
    graph.add_conditional_edges("compliance_input", route_input_risk)
    graph.add_edge("classify_intent", "extract_slots")
    graph.add_edge("extract_slots", "validate_slots")
    graph.add_conditional_edges("validate_slots", route_business_intent)
    graph.add_edge("retrieve_products", "recommend")
    graph.add_edge("recommend", "generate_answer")
    graph.add_edge("retrieve_knowledge", "generate_answer")
    graph.add_edge("query_orders", "generate_answer")
    graph.add_edge("generate_answer", "compliance_output")
    graph.add_edge("compliance_output", "persist_memory")
    graph.add_edge("persist_memory", "write_trace")
    graph.add_edge("write_trace", END)
    return graph.compile()
~~~

## 9. 槽位合并和偏好修改

规则不能直接覆盖用户意图，槽位需要带操作类型。

~~~python
def merge_slots(old_slots, new_slots, operations):
    merged = dict(old_slots)

    for name, value in new_slots.items():
        operation = operations.get(name, "SET")

        if operation == "SET":
            merged[name] = value
        elif operation == "APPEND":
            merged[name] = unique(merged.get(name, []) + as_list(value))
        elif operation == "REMOVE":
            merged[name] = [
                x for x in merged.get(name, [])
                if x not in as_list(value)
            ]
        elif operation == "RESET":
            merged.pop(name, None)

    return merged


def validate_slots(intent, slots):
    required = clarify_schema.required_slots(intent, slots.get("category"))
    return [slot for slot in required if not slots.get(slot)]
~~~

## 10. 商品 Embedding、检索和画像重排

~~~python
def index_product(product):
    text = ProductTextBuilder.build(product)
    vector_store.upsert(
        id=f"product:{product.id}",
        vector=embedding_model.embed(text),
        metadata={
            "product_id": product.id,
            "category": product.category,
            "price": product.price,
            "brand": product.brand,
            "stock": product.stock,
        },
    )


def search_products(query, slots, user_profile):
    candidates = vector_store.search(
        embedding_model.embed(query),
        top_k=30,
    )
    candidates = [
        item for item in candidates
        if structured_filter(item, slots)
        and item.metadata["stock"] > 0
    ]

    for item in candidates:
        item.final_score = (
            0.55 * item.semantic_score
            + 0.25 * profile_score(item, user_profile)
            + 0.20 * business_score(item, slots)
        )

    return sorted(
        candidates,
        key=lambda item: item.final_score,
        reverse=True,
    )[:5]
~~~

当前 app/rag.py 的 TF-IDF 只能作为离线 fallback，生产实现应替换为真实 Embedding + pgvector、FAISS 或 Milvus。

## 11. RAG 和 Embedding 入库

~~~python
def ingest_document(path, knowledge_type, version):
    raw_text = document_parser.read(path)
    clean_text = normalize_text(raw_text)
    chunks = chunker.split(
        clean_text,
        max_tokens=500,
        overlap_tokens=80,
        keep_heading=True,
    )

    for index, chunk in enumerate(chunks):
        vector_store.upsert(
            id=stable_hash(path, version, index),
            vector=embedding_model.embed(chunk.text),
            document=chunk.text,
            metadata={
                "source": path.name,
                "knowledge_type": knowledge_type,
                "version": version,
                "chunk_index": index,
                "content_hash": sha256(chunk.text),
            },
        )


def answer_with_rag(query, session_context):
    hits = vector_store.search(
        embedding_model.embed(query),
        top_k=8,
        filters=tenant_filter(),
    )
    hits = [hit for hit in hits if hit.score >= settings.rag_min_score]

    if not hits:
        return fallback_answer("NO_KNOWLEDGE_EVIDENCE")

    context = assemble_context(hits, max_tokens=3500)
    answer = llm.generate(
        system=RAG_SYSTEM_PROMPT,
        input={"query": query, "context": context, "history": session_context},
    )

    citations = verify_citations(answer, hits)
    if citations.coverage < 0.8:
        return fallback_answer("INSUFFICIENT_CITATION")
    return {"answer": answer, "citations": citations.items}
~~~

FAQ 是 Frequently Asked Questions，例如配送、退换货、发票和保修。FAQ 应与商品索引分开：

~~~python
def upsert_faq(question, answer, category, version):
    text = f"问题：{question}\n答案：{answer}"
    vector_store.upsert(
        id=f"faq:{stable_hash(question, version)}",
        vector=embedding_model.embed(text),
        document=text,
        metadata={
            "knowledge_type": "faq",
            "category": category,
            "version": version,
            "status": "published",
        },
    )


def search_faq(query):
    return vector_store.search(
        embedding_model.embed(query),
        top_k=5,
        filters={"knowledge_type": "faq", "status": "published"},
    )
~~~

## 12. 订单状态和工具调用

~~~python
ORDER_TRANSITIONS = {
    "PENDING_PAYMENT": {"PAID", "CANCELLED"},
    "PAID": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"COMPLETED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def get_order_detail(user, order_id):
    order = order_repo.find_by_id(order_id)
    if not order or order.user_id != user.id:
        return ToolResult(ok=False, error_code="ORDER_NOT_FOUND")
    return ToolResult(ok=True, data=order)


def transition_order(user, order_id, target_status, idempotency_key):
    with transaction():
        order = get_owned_order(user.id, order_id)
        if idempotency_repo.exists(idempotency_key):
            return idempotency_repo.result(idempotency_key)
        if target_status not in ORDER_TRANSITIONS[order.status]:
            raise BusinessError("INVALID_ORDER_TRANSITION")

        update_order_status(order.id, target_status)
        audit_log("ORDER_STATUS_CHANGED", user.id, order.id, target_status)
        result = ToolResult(ok=True, data=order)
        idempotency_repo.save(idempotency_key, result)
        return result


def resolve_order_reference(query, session_state):
    candidates = order_repo.list_recent(session_state.user_id)
    return llm.resolve_reference(query, candidates)
~~~

## 13. 多 Agent 推荐

~~~python
async def parallel_recommend(query, candidates, profile):
    results = await gather(
        run_agent("price", query, candidates, profile),
        run_agent("scenario", query, candidates, profile),
        run_agent("quality", query, candidates, profile),
        run_agent("diversity", query, candidates, profile),
    )
    return rerank_with_business_constraints(
        merge_candidate_scores(results),
        profile,
    )


async def run_agent(name, query, candidates, profile):
    memory = agent_memory.load(name, profile.user_id)
    return await agent_registry[name].run(
        query=query,
        candidates=candidates,
        profile=profile,
        memory=memory,
    )
~~~

当前 Demo 的并行推荐是线程池评分模拟，不是完整的 AgentScope/消息总线协作。

## 14. WebSocket ASR/TTS 流式通信

~~~python
@websocket("/ws/voice")
async def voice_session(socket, user):
    session_id = await open_session(user.id)
    asr = asr_client.start_stream()
    tts = tts_client.start_stream()

    async for event in socket:
        if event.type == "audio_chunk":
            partial = await asr.push(event.bytes)
            await socket.send_json({
                "type": "asr_partial",
                "text": partial,
            })

        if event.type == "speech_end":
            query = await asr.finalize()
            result = await graph.ainvoke({
                "session_id": session_id,
                "query": query,
            })

            for sentence in sentence_split(result.answer):
                await socket.send_bytes(
                    await tts.synthesize(sentence)
                )

            await socket.send_json({
                "type": "answer_end",
                "citations": result.citations,
            })
~~~

## 15. 情绪、合规、画像和行为

~~~python
def process_emotion(query, session_id):
    emotion = emotion_agent.detect(
        query,
        recent_turns(session_id, "emotion"),
    )
    return {
        "label": emotion.label,
        "confidence": emotion.confidence,
        "response_style": style_for_emotion(emotion.label),
    }


def check_input_compliance(query):
    risk = policy_engine.scan(query)
    if risk.level == "blocked":
        return ToolResult(ok=False, error_code="INPUT_BLOCKED")
    return risk


def check_output_compliance(answer, evidence):
    if contains_sensitive_content(answer):
        return safe_template("OUTPUT_BLOCKED")
    if contains_unsupported_claim(answer, evidence):
        return safe_template("NO_EVIDENCE")
    return answer


def record_behavior(user_id, product_id, behavior, context):
    behavior_repo.insert(user_id, product_id, behavior, context)
    profile_event_bus.publish("USER_BEHAVIOR", {
        "user_id": user_id,
        "product_id": product_id,
        "behavior": behavior,
    })


def rebuild_profile(user_id):
    events = behavior_repo.list_recent(user_id, days=90)
    return profile_repo.upsert(
        user_id=user_id,
        preferred_categories=weighted_categories(events),
        price_range=weighted_price_range(events),
        preferred_brands=weighted_brands(events),
        negative_preferences=extract_negative_preferences(events),
    )
~~~

## 16. Trace、审计和评测

~~~python
@trace_node("classify_intent")
async def classify_intent_node(state):
    with trace_span("intent.classify") as span:
        span.set_input({"query_hash": sha256(state.query)})
        result = await classify_intent(state.session_id, state.query)
        span.set_output({
            "intent": result.intent,
            "confidence": result.confidence,
        })
        metrics.observe("intent_latency_ms", span.duration_ms)
        return {"intent_result": result}


def write_audit_event(state, event_type, payload):
    audit_repo.insert({
        "trace_id": state.trace_id,
        "session_id": state.session_id,
        "user_id": state.user_id,
        "event_type": event_type,
        "payload": redact_sensitive_fields(payload),
        "created_at": utcnow(),
    })


def evaluate_agent(dataset, agent_version):
    scores = []
    for case in dataset:
        result = run_case(case, agent_version)
        scores.append({
            "intent_correct": result.intent == case.expected_intent,
            "slot_f1": slot_f1(result.slots, case.expected_slots),
            "tool_correct": tool_match(result.tool_trace, case.expected_tools),
            "citation_coverage": citation_coverage(result),
            "task_completed": task_completed(result, case),
        })
    return aggregate(scores)


def regression_check(current, baseline):
    if current["task_completed"] < baseline["task_completed"] - 0.03:
        return "REGRESSION"
    if current["citation_coverage"] < baseline["citation_coverage"] - 0.05:
        return "REGRESSION"
    if current["tool_correct"] < baseline["tool_correct"] - 0.03:
        return "REGRESSION"
    return "PASS"
~~~

至少记录：节点耗时、模型/Embedding/检索耗时、意图置信度、槽位变化、工具调用、fallback、无证据回答、订单变更和模型版本。API Key、密码等敏感数据必须脱敏。

## 17. 部署伪代码

~~~yaml
services:
  api:
    build: .
    env_file: .env
    depends_on: [postgres, redis]

  postgres:
    image: postgres
    extensions: [pgvector]

  redis:
    image: redis

  worker:
    build: .
    command: python -m app.worker
~~~

需要的关键配置：

~~~text
LLM_API_KEY        通过环境变量或密钥管理器注入
LLM_MODEL          DeepSeek 模型名
DATABASE_URL       PostgreSQL 连接串
REDIS_URL          Redis 连接串
VECTOR_DATABASE    pgvector / Milvus / FAISS
JWT_SECRET         不进入 Git
ASR_ENDPOINT       真实语音识别服务
TTS_ENDPOINT       真实语音合成服务
~~~

## 18. 建议优先级

### P0：对话正确性

模型主意图、上下文修正、槽位增量合并、显式否定、结构化 ToolResult，以及订单/商品/FAQ 独立工具。

### P1：知识和推荐

真实 Embedding、向量库、商品向量索引、FAQ 独立索引、召回过滤和画像重排。

### P2：业务闭环

JWT、订单状态流转、订单详情、幂等操作、Redis 记忆、WebSocket ASR/TTS、情绪和合规。

### P3：工程化证明

完整 Trace、审计入库、Golden Dataset、Prompt A/B、回归、Red Team、延迟和 Token 指标。

## 19. 结论

当前目录足以支撑可运行、可展示的 Python Demo，但不能声称已完整复刻原始 VoiceShop。最重要的缺口是：

1. 模型负责意图，规则负责抽取和业务校验；
2. Embedding + 向量库负责语义召回，RAG 负责有证据回答；
3. 工具、订单和权限负责真实业务动作；
4. 记忆、Trace、评测和回归负责稳定运行。

本文给出了后续补齐时的模块边界，避免把所有逻辑继续堆进 app/graph.py。
