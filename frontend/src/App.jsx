import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function money(value) {
  if (value === null || value === undefined || value === "") return "Price unavailable";
  const n = Number(value);
  return Number.isFinite(n)
    ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n)
    : String(value);
}

function titleCase(value) {
  return String(value || "").replace(/[_-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function listValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === "string" && value.trim()) return value.split(/[,;]/).map((x) => x.trim()).filter(Boolean);
  return [];
}

function productName(item) {
  return item?.name || item?.product_name || item?.title || item?.product?.name || "Recommended product";
}

function productPrice(item) {
  return item?.price ?? item?.product?.price ?? item?.displayed_price;
}

function productSpecs(item) {
  const raw = item?.specifications || item?.specs || item?.product?.specifications || {};
  if (Array.isArray(raw)) return raw.map((x) => typeof x === "string" ? x : `${x.name || x.key || ""}${x.value ? `: ${x.value}` : ""}`).filter(Boolean);
  if (typeof raw === "string") return raw.split(/[;,|]/).map((x) => x.trim()).filter(Boolean);
  if (raw && typeof raw === "object") return Object.entries(raw).map(([k, v]) => `${titleCase(k)}: ${Array.isArray(v) ? v.join(", ") : v}`).filter((x) => !x.endsWith(": "));
  return [];
}

function getRecommendations(message) {
  const values = message?.recommendations || message?.products || message?.matches || message?.data?.recommendations;
  if (Array.isArray(values)) return values;

  // The current FastAPI endpoint returns grounded product matches in `reply` text.
  const reply = message?.reply || "";
  if (!/Here are your best matches:/i.test(reply)) return [];

  const blocks = reply.split(/\n(?=\s*\d+\.\s+)/).filter((part) => /^\s*\d+\.\s+/.test(part));
  return blocks.map((block, index) => {
    const lines = block.split("\n");
    const firstLine = lines[0].match(/^\s*\d+\.\s+(.+?)\s+—\s+₹([\d,]+)/);
    if (!firstLine) return null;
    const details = lines.slice(1).join(" ").trim();
    const specsMatch = details.match(/Key specifications:\s*(\{.*\})/);
    const specifications = specsMatch
      ? { "Key specifications": specsMatch[1].replace(/[{}']/g, "").replace(/,\s*/g, " · ") }
      : {};
    return {
      product_id: `reply-product-${index}`,
      name: firstLine[1].trim(),
      price: Number(firstLine[2].replace(/,/g, "")),
      explanation: details.replace(/Key specifications:\s*\{.*\}/, "").trim(),
      specifications,
    };
  }).filter(Boolean);
}

function getAssistantText(message) {
  if (typeof message === "string") return message;
  return message?.reply || message?.content || message?.message || message?.response || message?.text || "";
}

function RequirementCard({ requirements }) {
  const req = requirements || {};
  const uses = listValue(req.intended_uses || req.uses);
  const preferences = listValue(req.preferences);
  const budget = req.max_budget ?? req.budget ?? req.max_price;
  return (
    <section className="requirements-card">
      <div className="section-kicker"><span className="status-dot" /> YOUR SEARCH</div>
      <h2>What matters to you</h2>
      <div className="requirement-line">
        <span className="requirement-icon">⌘</span>
        <div><span className="field-label">Category</span><strong>{req.category ? titleCase(req.category) : "Not selected"}</strong></div>
      </div>
      <div className="requirement-line">
        <span className="requirement-icon">₹</span>
        <div><span className="field-label">Maximum budget</span><strong>{budget !== undefined && budget !== null ? money(budget) : "Flexible"}</strong></div>
      </div>
      <div className="requirement-group">
        <span className="field-label">Intended use</span>
        <div className="chips">{uses.length ? uses.map((x) => <span className="chip" key={x}>{titleCase(x)}</span>) : <span className="muted">Add how you plan to use it</span>}</div>
      </div>
      <div className="requirement-group">
        <span className="field-label">Preferences</span>
        <div className="chips">{preferences.length ? preferences.map((x) => <span className="chip chip-muted" key={x}>{titleCase(x)}</span>) : <span className="muted">No preferences yet</span>}</div>
      </div>
      <div className="privacy-note"><span>✦</span> Recommendations are selected from your product catalogue.</div>
    </section>
  );
}

function ProductCard({ product, index }) {
  const name = productName(product);
  const specs = productSpecs(product);
  const explanation = product?.explanation || product?.reason || product?.justification || product?.match_reason || "";
  const category = product?.category || product?.product?.category;
  const uses = listValue(product?.matched_uses || product?.matching_uses);
  return (
    <article className="product-card">
      <div className="product-topline">
        <span className="product-index">{String(index + 1).padStart(2, "0")}</span>
        <span className="product-tag">{category ? titleCase(category) : "Recommended match"}</span>
      </div>
      <div className="product-main">
        <div className="product-illustration" aria-hidden="true">
          {String(category || "").toLowerCase().includes("laptop") ? "▱" :
           String(category || "").toLowerCase().includes("phone") ? "▯" :
           String(category || "").toLowerCase().includes("head") ? "◖◗" :
           String(category || "").toLowerCase().includes("monitor") ? "▣" : "◇"}
        </div>
        <div className="product-heading">
          <h3>{name}</h3>
          <div className="product-price">{money(productPrice(product))}</div>
          {product?.brand && <p className="product-brand">{product.brand}</p>}
        </div>
      </div>
      {explanation && <p className="product-reason">{explanation}</p>}
      {uses.length > 0 && <div className="chips product-chips">{uses.map((x) => <span className="chip" key={x}>{titleCase(x)}</span>)}</div>}
      {specs.length > 0 && (
        <div className="spec-grid">
          {specs.slice(0, 4).map((spec, i) => <div className="spec-item" key={`${spec}-${i}`}><span className="spec-mark">✓</span><span>{spec}</span></div>)}
        </div>
      )}
      {product?.score !== undefined && <div className="match-footer"><span>Match score</span><strong>{Math.round(Number(product.score) * (Number(product.score) <= 1 ? 100 : 1))}%</strong></div>}
    </article>
  );
}

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [requirements, setRequirements] = useState({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState("checking");
  const [showMobileRequirements, setShowMobileRequirements] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/health`)
      .then((r) => { if (!r.ok) throw new Error(); setHealth("online"); })
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function newConversation() {
    setConversationId(null);
    setMessages([]);
    setRequirements({});
    setInput("");
    setError("");
    setShowMobileRequirements(false);
    inputRef.current?.focus();
  }

  async function sendMessage(event) {
    event?.preventDefault();
    const content = input.trim();
    if (!content || loading) return;
    setError("");
    setInput("");
    setMessages((old) => [...old, { role: "user", content, localId: `${Date.now()}-user` }]);
    setLoading(true);

    try {
      let id = conversationId;
      if (!id) {
        const createResponse = await fetch(`${API_BASE}/api/v1/conversations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        if (!createResponse.ok) throw new Error(`Could not start a conversation (${createResponse.status}).`);
        const created = await createResponse.json();
        id = created.id || created.conversation_id || created.conversation?.id;
        if (!id) throw new Error("The server started a conversation but did not return its ID.");
        setConversationId(id);
      }

      const response = await fetch(`${API_BASE}/api/v1/conversations/${id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status}).`);
      const updatedRequirements = data.requirements || data.current_requirements || data.conversation?.current_requirements;
      if (updatedRequirements) setRequirements(updatedRequirements);

      const recommendations = getRecommendations(data);
      const assistantContent = recommendations.length
        ? (data.reply?.split(/\n\s*\d+\.\s+/)[0] || "Here are your best matches.").trim()
        : getAssistantText(data) || "I've updated your requirements.";
      const assistantMessage = {
        role: "assistant",
        content: assistantContent,
        recommendations,
        localId: `${Date.now()}-assistant`,
      };
      setMessages((old) => [...old, assistantMessage]);
    } catch (err) {
      setError(err?.message || "Something went wrong. Please try again.");
      setMessages((old) => old.filter((m) => !String(m.localId || "").endsWith("-user") || m.content !== content));
      setInput(content);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  const starterPrompts = [
    "I need a laptop for college under ₹80,000",
    "Recommend headphones for commuting",
    "I need a monitor for programming",
  ];

  return (
    <div className="app-shell">
      <aside className="left-rail">
        <div className="brand-lockup">
          <div className="brand-mark">e<span>.</span></div>
          <div><strong>electra</strong><small>SMART BUYING, SIMPLIFIED</small></div>
        </div>
        <button className="new-chat-button" onClick={newConversation}><span className="plus">＋</span> New conversation</button>
        <div className="rail-label">YOUR ASSISTANT</div>
        <div className="rail-feature"><span className="rail-feature-icon">✦</span><div><strong>Product finder</strong><small>Personalized recommendations</small></div></div>
        <div className="rail-bottom">
          <div className={`connection-pill ${health}`}><span />{health === "online" ? "API connected" : health === "offline" ? "API unavailable" : "Connecting to API"}</div>
          <p>Grounded in your catalogue.<br />Built to respect your budget.</p>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <div className="eyebrow">YOUR PERSONAL TECH GUIDE</div>
            <h1>Find your next <span>favourite.</span></h1>
            <p>Tell me what you need. I'll help narrow down the right tech for you.</p>
          </div>
          <button className="mobile-requirements-button" onClick={() => setShowMobileRequirements((v) => !v)}>Search details</button>
          <div className="topbar-badge"><span className="sparkle">✦</span><div><strong>Thoughtful picks</strong><small>Based on your needs</small></div></div>
        </header>

        <div className="main-grid">
          <section className="chat-panel">
            <div className="chat-header">
              <div className="assistant-avatar">e<span>.</span></div>
              <div className="chat-header-copy"><strong>Electra assistant</strong><span><i /> Ready to help you choose</span></div>
              <span className="chat-header-label">AI SHOPPING GUIDE</span>
            </div>
            <div className="chat-feed">
              {messages.length === 0 ? (
                <div className="welcome-state">
                  <div className="welcome-orbit"><span>✦</span><i>⌁</i><b>◈</b></div>
                  <div className="eyebrow">LET'S FIND YOUR MATCH</div>
                  <h2>Good tech starts<br />with <span>your needs.</span></h2>
                  <p>Share a product type, budget, and what you want to do with it. We can refine your choices as we go.</p>
                  <div className="starter-list">
                    <span className="field-label">TRY ASKING</span>
                    {starterPrompts.map((prompt) => <button className="starter-prompt" key={prompt} onClick={() => { setInput(prompt); inputRef.current?.focus(); }}>{prompt}<span>↗</span></button>)}
                  </div>
                </div>
              ) : (
                <div className="message-list">
                  {messages.map((message) => (
                    <div className={`message-row ${message.role}`} key={message.localId || `${message.role}-${message.content}`}>
                      {message.role === "assistant" && <div className="message-avatar">e.</div>}
                      <div className="message-content">
                        <div className="message-author">{message.role === "user" ? "You" : "Electra"}</div>
                        <div className="message-bubble">{message.content}</div>
                        {message.recommendations?.length > 0 && (
                          <div className="recommendation-list">
                            <div className="recommendation-heading"><div><span className="eyebrow">PICKED FOR YOU</span><h3>Your best matches</h3></div><span className="result-count">{message.recommendations.length} PICKS</span></div>
                            {message.recommendations.map((product, i) => <ProductCard product={product} index={i} key={product.product_id || product.id || productName(product) + i} />)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && <div className="message-row assistant"><div className="message-avatar">e.</div><div className="message-content"><div className="message-author">Electra</div><div className="typing-bubble"><span /><span /><span /> Finding a thoughtful match…</div></div></div>}
                  <div ref={endRef} />
                </div>
              )}
            </div>
            {error && <div className="error-banner"><span>!</span><div><strong>Message not sent</strong><p>{error}</p></div><button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
            <form className="composer" onSubmit={sendMessage}>
              <div className="composer-inner">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(e); } }}
                  placeholder="Tell me what you're looking for…"
                  rows={1}
                  maxLength={4000}
                  disabled={loading}
                />
                <button className="send-button" type="submit" disabled={!input.trim() || loading} aria-label="Send message">↑</button>
              </div>
              <div className="composer-foot"><span><kbd>Enter</kbd> to send <span className="dot-separator">·</span> <kbd>Shift + Enter</kbd> for a new line</span><span>{input.length}/4000</span></div>
            </form>
          </section>

          <aside className={`requirements-column ${showMobileRequirements ? "mobile-visible" : ""}`}>
            <RequirementCard requirements={requirements} />
            <section className="tips-card">
              <div className="tips-icon">✧</div>
              <h3>A better recommendation</h3>
              <p>Specific details help us compare products more meaningfully.</p>
              <div className="tip-example"><span>Try adding</span><strong>“I need it for local machine learning.”</strong></div>
            </section>
            <div className="trust-note"><span>⌁</span><p><strong>No made-up products.</strong><br />Matches come from the catalogue and are filtered against your budget.</p></div>
          </aside>
        </div>
        <footer className="page-footer"><span>Electra · Electronics Recommendation Agent</span><span>Built for more confident choices <b>✦</b></span></footer>
      </main>
    </div>
  );
}
