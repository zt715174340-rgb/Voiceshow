# VoiceShop AI

基于 Python 与 LangGraph 构建的 AI 语音导购系统，面向商品咨询、智能推荐、知识问答与订单服务等购物场景。

## Project capabilities

- 基于 LangGraph 编排多轮购物对话，支持意图识别、上下文理解、槽位提取与澄清
- 结合大模型判断用户主要意图，并通过结构化工具完成商品检索、价格查询、订单查询和偏好调整
- 支持商品目录、商品详情、浏览行为、购物车式订单创建与订单管理
- 支持产品手册、配送政策、售后规则等知识内容的解析、检索、答案生成与来源引用
- 支持多角度商品推荐、预算和场景匹配，以及推荐结果的解释生成
- 支持用户画像、购买行为、会话消息、FAQ、订单和 Trace 数据持久化
- 支持浏览器语音输入与语音回复，提供自然语言导购交互
- 支持离线问答评测、召回质量评估、工具调用记录和流程审计
- 对超出结构化业务流程的问题调用兼容 OpenAI API 的大模型进行处理

## Architecture

```text
app/
├── agent/          # 意图、澄清、情绪、推荐与多视角 Agent
├── compliance/     # 输入输出安全与证据校验
├── config/         # 模型、数据库、缓存和向量服务配置
├── controller/     # 对话、商品、订单和语音接口
├── dto/             # 请求、响应和 Agent 结果结构
├── entity/          # 用户、商品、订单、会话和知识实体
├── event/           # 用户行为、订单和 Trace 领域事件
├── listener/        # 异步画像、审计和事件处理
├── memory/          # 会话记忆、摘要和 Agent 记忆策略
├── repository/      # 商品、订单、知识库和向量数据访问
├── security/        # 登录认证、JWT 和资源权限校验
├── service/         # 对话编排、推荐、订单和知识服务
└── voice/           # ASR/TTS 流式通信
```

系统以 LangGraph 作为流程编排层，将意图识别、槽位更新、知识检索、商品工具、推荐聚合、合规检查和 Trace 记录组织为可追踪的状态流转。

## Run

```bash
cd G:\ai-agent-show\voiceshop-ai
python -m app.web
```

Open `http://127.0.0.1:7860`.

## LLM configuration

The service uses an OpenAI-compatible model for intent understanding and open-ended questions:

```text
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

`OPENAI_API_KEY` is also supported. Do not commit keys or the local `data/voiceshop.db` file.

## Conversation and FAQ

The browser stores a `session_id` and sends it with each request. The backend persists
messages and extracted slots, so a follow-up such as `预算 500 以内` can complete the
previous request for shoes. FAQ means frequently asked questions, such as delivery,
returns and exchanges. Those questions now enter the RAG flow: knowledge files are
split into chunks, locally ranked, assembled as context, and optionally summarized by
the configured DeepSeek model with a source filename.
