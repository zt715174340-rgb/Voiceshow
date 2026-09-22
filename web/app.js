const queryInput = document.querySelector("#query");
const runButton = document.querySelector("#runButton");
const speakButton = document.querySelector("#speakButton");
const evalButton = document.querySelector("#evalButton");
const answerTitle = document.querySelector("#answerTitle");
const answerText = document.querySelector("#answerText");
const thinkingText = document.querySelector("#thinkingText");
const micButton = document.querySelector("#micButton");
const voiceStatus = document.querySelector("#voiceStatus");
const userChat = document.querySelector(".user-chat");
const recommendationList = document.querySelector("#recommendationList");
const recommendationCount = document.querySelector("#assistantRecommendationCount");
const catalogGrid = document.querySelector("#catalogGrid");
const catalogSummary = document.querySelector("#catalogSummary");
const catalogTitle = document.querySelector("#catalogTitle");
const sortChip = document.querySelector("#sortChip");
const candidateCount = document.querySelector("#candidateCount");
const slotCount = document.querySelector("#slotCount");
const traceCount = document.querySelector("#traceCount");
const slotList = document.querySelector("#slotList");
const traceList = document.querySelector("#traceList");
const traceId = document.querySelector("#traceId");
const metricGrid = document.querySelector("#metricGrid");
const productDetail = document.querySelector("#productDetail");
const conversationMessages = document.querySelector("#conversationMessages");
const detailName = document.querySelector("#detailName");
const detailDescription = document.querySelector("#detailDescription");
const detailPrice = document.querySelector("#detailPrice");
const detailOrderButton = document.querySelector("#detailOrderButton");
const orderList = document.querySelector("#orderList");

let latestResponse = "";
let allProducts = [];
let activeCategory = "全部";
let sessionId = window.localStorage.getItem("voiceshop_session_id") || null;
let recognition = null;
let isListening = false;

const slotLabels = { category: "商品类别", budget_max: "预算上限", usage_scene: "使用场景", brand_preference: "品牌偏好", must_have: "核心偏好", avoid: "规避条件" };
const metricLabels = { total_cases: "评测样本", slot_f1: "Slot-F1", recall_at_5: "Recall@5", clarification_accuracy: "澄清准确率" };

function switchView(viewName) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => panel.classList.toggle("active", panel.id === viewName));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === viewName));
  history.replaceState(null, "", `#${viewName}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function formatValue(value) {
  if (Array.isArray(value)) return value.length ? value.join("、") : "未命中";
  if (value === null || value === undefined || value === "") return "未识别";
  return String(value);
}

function visualClass(category = "") {
  if (category.includes("耳机")) return "headphone-visual";
  if (category.includes("手表")) return "watch-visual";
  if (category.includes("口红")) return "lipstick-visual";
  return "shoe-visual";
}

function activeSlotCount(slots = {}) {
  return Object.values(slots).filter((value) => Array.isArray(value) ? value.length : value !== null && value !== undefined && value !== "").length;
}

function renderSlots(slots = {}) {
  slotCount.textContent = activeSlotCount(slots);
  slotList.innerHTML = Object.entries(slotLabels).map(([key, label]) => {
    const value = key === "budget_max" && slots[key] ? `${slots[key]} 元` : formatValue(slots[key]);
    return `<div><dt>${label}</dt><dd>${value}</dd></div>`;
  }).join("");
}

function buildReason(item, slots = {}) {
  const reasons = [];
  if (slots.budget_max && item.price <= slots.budget_max) reasons.push(`价格 ${item.price} 元，在预算内`);
  if (slots.usage_scene && (item.scene_tags || []).includes(slots.usage_scene)) reasons.push("使用场景匹配");
  const matched = (slots.must_have || []).filter((tag) => (item.feature_tags || []).includes(tag));
  if (matched.length) reasons.push(`命中${matched.join("、")}偏好`);
  if (item.stock > 0) reasons.push("当前有库存");
  return reasons.length ? reasons.join(" · ") : "综合匹配度较高，适合作为候选商品";
}

function productCard(item, mode = "catalog", slots = {}) {
  const score = item.score ? `<span class="score">匹配度 ${Number(item.score).toFixed(2)}</span>` : "";
  const reason = mode === "recommendation" ? `<p class="reason">推荐理由：${buildReason(item, slots)}</p>` : "";
  return `<article class="${mode === "catalog" ? "catalog-card" : "product-card"}">
    <div class="visual"><div class="product-visual ${visualClass(item.category)}"></div></div>
    <div>${score}<h3>${item.name}</h3></div>
    <div class="price-line"><span class="price">${item.price} 元</span><span class="stock">库存 ${item.stock}</span></div>
    <div class="meta"><span>${item.brand}</span><span>${item.category}</span>${(item.scene_tags || []).slice(0, 2).map((tag) => `<span>${tag}</span>`).join("")}</div>
    <p>${item.description}</p>${reason}<div class="product-actions"><button type="button" data-product-view="${item.id}">查看详情</button><button type="button" data-product-order="${item.id}">立即下单</button></div>
  </article>`;
}

function renderCatalog() {
  const products = activeCategory === "全部" ? allProducts : allProducts.filter((item) => item.category === activeCategory);
  catalogTitle.textContent = activeCategory === "全部" ? "全部商品" : activeCategory;
  catalogSummary.textContent = `${products.length} 件商品`;
  sortChip.textContent = "精选商品";
  catalogGrid.innerHTML = products.length ? products.map((item) => productCard(item)).join("") : "<div class='catalog-empty'>暂时没有符合条件的商品</div>";
}

function showProductDetail(productId) {
  const item = allProducts.find((product) => product.id === Number(productId));
  if (!item) return;
  if (!productDetail.querySelector("[data-detail-close]")) {
    productDetail.insertAdjacentHTML("afterbegin", '<button class="detail-close" type="button" data-detail-close aria-label="关闭商品详情">×</button>');
  }
  detailName.textContent = item.name;
  detailDescription.innerHTML = `<strong>${item.brand} · ${item.category}</strong><br>${item.description}<br><span>适用场景：${(item.scene_tags || []).join("、") || "日常使用"}　|　功能特点：${(item.feature_tags || []).join("、") || "基础功能"}　|　库存：${item.stock} 件</span>`;
  detailPrice.textContent = `${item.price} 元`;
  detailOrderButton.dataset.productId = item.id;
  productDetail.classList.remove("is-hidden");
  switchView("catalog");
  productDetail.scrollIntoView({ behavior: "smooth", block: "center" });
  fetch("/api/behavior", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ product_id: item.id, event: "view" }) });
}

async function createOrder(productId) {
  const response = await fetch("/api/orders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ product_id: Number(productId), session_id: sessionId }) });
  if (!response.ok) throw new Error("订单创建失败");
  await loadOrders();
  switchView("orders");
}

async function loadOrders() {
  const data = await (await fetch("/api/orders")).json();
  orderList.innerHTML = data.orders.length ? data.orders.map((order) => `<article class="order-item"><div><strong>${order.order_no}</strong><span>商品 ID ${order.product_id} · ${order.quantity} 件</span></div><div class="order-actions"><b>${order.status}</b><button type="button" data-order-delete="${order.order_no}">删除订单</button></div></article>`).join("") : "<div class='catalog-empty'>暂时还没有订单</div>";
}

async function deleteOrder(orderNo) {
  const response = await fetch("/api/orders/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ order_no: orderNo }) });
  if (!response.ok) throw new Error("订单删除失败");
  await loadOrders();
}

function renderRecommendations(items = [], slots = {}) {
  candidateCount.textContent = items.length;
  recommendationCount.textContent = items.length ? `${items.length} 件推荐` : "尚未筛选";
  if (!items.length) {
    recommendationList.className = "recommendation-list empty";
    recommendationList.textContent = "你的推荐商品会显示在这里";
    return;
  }
  recommendationList.className = "recommendation-list";
  recommendationList.innerHTML = items.map((item) => productCard(item, "recommendation", slots)).join("");
}

function summarizeTraceStep(step) {
  if (step.node === "extract_slots") return `识别 ${activeSlotCount(step.slots || {})} 组需求`;
  if (step.node === "clarification_gate") return step.need_clarification ? "缺少关键信息，向用户追问" : "需求完整，进入商品召回";
  if (step.node === "retrieve_products") return `召回 ${step.candidate_count || 0} 个候选商品`;
  if (step.node === "generate_recommendation") return `输出 Top ${step.top_ids?.length || 0} 推荐`;
  return step.node;
}

function renderTrace(result) {
  const trace = result.trace || [];
  traceCount.textContent = trace.length;
  traceId.textContent = result.trace_id ? `trace ${result.trace_id.slice(0, 8)}` : "trace pending";
  traceList.innerHTML = trace.map((step, index) => `<li><strong>${index + 1}. ${step.label || step.node}</strong><span>${summarizeTraceStep(step)}</span><code>${JSON.stringify(step, null, 2)}</code></li>`).join("");
}

function renderResult(result) {
  latestResponse = result.response || "";
  const slots = result.slots || {};
  answerTitle.textContent = result.status === "clarify" ? "还需要一点信息" : (result.recommendations?.length ? "已完成筛选" : "知识库回答");
  answerText.textContent = latestResponse || "没有返回内容";
  userChat.textContent = queryInput.value.trim();
  renderSlots(slots);
  renderRecommendations(result.recommendations || [], slots);
  renderTrace(result);
}

function appendConversationMessage(className, text, thinking = false) {
  const message = document.createElement("div");
  message.className = `message ${className}`;
  if (thinking) {
    message.innerHTML = `${text}<span class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></span>`;
  } else {
    message.textContent = text;
  }
  conversationMessages.appendChild(message);
  conversationMessages.scrollTop = conversationMessages.scrollHeight;
  return message;
}

function hideLegacyMessagePlaceholders() {
  userChat.classList.add("is-hidden");
  thinkingText.classList.add("is-hidden");
  answerText.classList.add("is-hidden");
}

async function runAgent() {
  const query = queryInput.value.trim();
  if (!query) return;
  runButton.disabled = true;
  hideLegacyMessagePlaceholders();
  appendConversationMessage("user-chat", query);
  const thinkingMessage = appendConversationMessage("thinking-chat", "Agent 正在分析", true);
  runButton.innerHTML = "正在筛选 <span>…</span>";
  userChat.textContent = query;
  userChat.classList.remove("is-hidden");
  userChat.classList.add("is-hidden");
  answerText.classList.add("is-hidden");
  thinkingText.classList.remove("is-hidden");
  thinkingText.classList.add("is-hidden");
  answerTitle.textContent = "Agent 正在分析";
  recommendationCount.textContent = "分析中";
  renderRecommendations([]);
  const startedAt = Date.now();
  try {
    const responsePromise = fetch("/api/recommend", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, session_id: sessionId }) });
    const response = await responsePromise;
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "推荐失败");
    sessionId = result.session_id || sessionId;
    if (sessionId) window.localStorage.setItem("voiceshop_session_id", sessionId);
    await new Promise((resolve) => setTimeout(resolve, Math.max(0, 850 - (Date.now() - startedAt))));
    thinkingText.classList.add("is-hidden");
    answerText.classList.remove("is-hidden");
    thinkingMessage.remove();
    answerText.classList.add("is-hidden");
    appendConversationMessage("assistant-chat", result.response || "没有返回内容");
    renderResult(result);
  } catch (error) {
    thinkingText.classList.add("is-hidden");
    answerText.classList.remove("is-hidden");
    thinkingMessage.remove();
    answerText.classList.add("is-hidden");
    appendConversationMessage("assistant-chat", error.message);
    answerTitle.textContent = "暂时无法完成筛选";
    answerText.textContent = error.message;
    renderRecommendations([]);
  } finally {
    runButton.disabled = false;
    runButton.innerHTML = "开始筛选 <span>↗</span>";
  }
}

function speakLatestResponse() {
  if (!latestResponse) return;
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(latestResponse);
  utterance.lang = "zh-CN";
  window.speechSynthesis.speak(utterance);
}

function setVoiceStatus(message) {
  voiceStatus.textContent = message;
}

function toggleVoiceInput() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    setVoiceStatus("当前浏览器不支持语音识别，请使用文字输入");
    return;
  }
  if (isListening) {
    recognition.stop();
    return;
  }

  const originalText = queryInput.value.trim() === "今天我想买个鞋子" ? "" : queryInput.value.trim();
  recognition = new Recognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.onstart = () => {
    isListening = true;
    micButton.classList.add("listening");
    micButton.setAttribute("aria-pressed", "true");
    micButton.setAttribute("aria-label", "停止语音输入");
    setVoiceStatus("正在聆听，请说出你的需求…");
  };
  recognition.onresult = (event) => {
    const transcript = Array.from(event.results).map((result) => result[0].transcript).join("");
    queryInput.value = [originalText, transcript].filter(Boolean).join("，");
  };
  recognition.onerror = (event) => {
    setVoiceStatus(event.error === "not-allowed" ? "麦克风权限未开启，请允许浏览器使用麦克风" : "没有听清，可以再说一次");
  };
  recognition.onend = () => {
    isListening = false;
    micButton.classList.remove("listening");
    micButton.setAttribute("aria-pressed", "false");
    micButton.setAttribute("aria-label", "开始语音输入");
    if (queryInput.value.trim()) setVoiceStatus("已识别，可以检查内容后发送");
  };
  recognition.start();
}

async function refreshEval() {
  evalButton.disabled = true;
  try {
    const report = await (await fetch("/api/eval")).json();
    metricGrid.innerHTML = Object.entries(metricLabels).map(([key, label]) => {
      const raw = report[key];
      const value = typeof raw === "number" && raw <= 1 ? raw.toFixed(4) : raw;
      return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
    }).join("");
  } finally {
    evalButton.disabled = false;
  }
}

async function loadCatalog() {
  const data = await (await fetch("/api/products")).json();
  allProducts = data.products || [];
  renderCatalog();
}

document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
document.querySelectorAll("[data-query]").forEach((button) => button.addEventListener("click", () => { queryInput.value = button.dataset.query; switchView("dialogue"); runAgent(); }));
document.querySelectorAll("[data-category]").forEach((button) => button.addEventListener("click", () => {
  activeCategory = button.dataset.category;
  document.querySelectorAll("[data-category]").forEach((item) => item.classList.toggle("active", item === button));
  renderCatalog();
}));
document.addEventListener("click", (event) => {
  const detailClose = event.target.closest("[data-detail-close]");
  if (detailClose || event.target === productDetail) productDetail.classList.add("is-hidden");
  const detailButton = event.target.closest("[data-product-view]");
  const orderButton = event.target.closest("[data-product-order]");
  if (detailButton) showProductDetail(detailButton.dataset.productView);
  if (orderButton) createOrder(orderButton.dataset.productOrder).catch((error) => { answerText.textContent = error.message; });
  const deleteButton = event.target.closest("[data-order-delete]");
  if (deleteButton) deleteOrder(deleteButton.dataset.orderDelete).catch((error) => { orderList.insertAdjacentHTML("afterbegin", `<div class='catalog-empty'>${error.message}</div>`); });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") productDetail.classList.add("is-hidden");
});
detailOrderButton.addEventListener("click", () => createOrder(detailOrderButton.dataset.productId));

runButton.addEventListener("click", runAgent);
speakButton.addEventListener("click", speakLatestResponse);
micButton.addEventListener("click", toggleVoiceInput);
evalButton.addEventListener("click", refreshEval);
queryInput.addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) runAgent(); });

const initialView = window.location.hash.slice(1);
if (["dialogue", "catalog", "scenes", "orders"].includes(initialView)) switchView(initialView);
loadCatalog();
loadOrders();
refreshEval();
