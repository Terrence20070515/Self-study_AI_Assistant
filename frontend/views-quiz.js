/* 出题与对话域：一键出题 / 问答面板 / 设置 */
// ---------- 出题 ----------
$("#btn-toggle-quiz-scope").onclick = () => $("#quiz-scope").classList.toggle("hidden");

function quizCandidates() {
  return materialState.list.filter(m => m.status === "ready" && (!quizState.scopeTag || m.tag === quizState.scopeTag));
}

function renderQuizScope() {
  const box = $("#quiz-material-list");
  if (!box) return;
  const list = quizCandidates();
  box.innerHTML = "";
  for (const m of list) {
    const label = document.createElement("label");
    label.title = m.orig_name;
    label.innerHTML = `<input type="checkbox" value="${m.id}" ${quizState.selected.has(m.id) ? "checked" : ""}>
      <span>${esc(m.orig_name)}</span>`;
    label.querySelector("input").onchange = (e) => {
      e.target.checked ? quizState.selected.add(m.id) : quizState.selected.delete(m.id);
      updateScopeCount();
    };
    box.appendChild(label);
  }
  // 清掉已不在列表里的选中项
  const ids = new Set(list.map(m => m.id));
  for (const id of [...quizState.selected]) if (!ids.has(id)) quizState.selected.delete(id);
  updateScopeCount();
}

function updateScopeCount() {
  const el = $("#quiz-scope-count");
  if (el) el.textContent = `已选 ${quizState.selected.size} 份资料`;
}

$("#quiz-tag-filter").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  quizState.scopeTag = chip.dataset.tag;
  document.querySelectorAll("#quiz-tag-filter .chip").forEach(c => c.classList.toggle("active", c === chip));
  renderQuizScope();
});
$("#btn-quiz-all").onclick = () => { quizCandidates().forEach(m => quizState.selected.add(m.id)); renderQuizScope(); };
$("#btn-quiz-none").onclick = () => { quizState.selected.clear(); renderQuizScope(); };

$("#btn-quiz").onclick = async () => {
  if (materialState.busy) return;
  const ids = [...quizState.selected];
  if (!ids.length) return toast("请先点「选择范围」勾选资料");
  const num = $("#quiz-num").value;
  const kind = $("#quiz-kind").value;
  const box = $("#quiz-result");
  materialState.busy = true;
  box.innerHTML = `<div class="quiz-empty">⏳ 正在基于所选 ${ids.length} 份资料出题…</div>`;
  try {
    const r = await api(`/api/courses/${courseState.currentId}/quiz`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ material_ids: ids, num: Number(num), kind }),
    });
    renderQuiz(r.questions || []);
    if (!r.questions?.length) box.innerHTML = `<div class="quiz-empty">没有生成题目，换个范围试试</div>`;
  } catch (err) {
    box.innerHTML = `<div class="quiz-empty">${esc(err.message)}</div>`;
  } finally {
    materialState.busy = false;
  }
};

function renderQuiz(questions) {
  const box = $("#quiz-result");
  box.innerHTML = "";
  questions.forEach((q, i) => {
    const card = document.createElement("div");
    card.className = "quiz-card";
    const opts = (q.options || []).map(o => `<div>${esc(o)}</div>`).join("");
    card.innerHTML = `
      <div class="q-title">${i + 1}. ${esc(q.question)}</div>
      ${opts ? `<div class="q-opts">${opts}</div>` : ""}
      <div class="q-actions">
        <button class="btn btn-outline btn-sm btn-show">显示答案</button>
        <span class="q-refs">${q.refs.map(r =>
          `<a class="cite" href="javascript:void(0)" data-mid="${r.material_id}" data-page="${r.page}" data-ext="${r.ext || "pdf"}">${esc(r.orig_name)} · ${unitLabel(r.ext, r.page)}</a>`
        ).join(" ")}</span>
      </div>
      <div class="q-ans hidden"><b>答案：</b>${esc(q.answer)}<br><b>解析：</b>${esc(q.explanation)}</div>`;
    card.querySelectorAll(".q-refs .cite").forEach(a => {
      a.onclick = () => openViewer(a.dataset.mid, Number(a.dataset.page), "", a.dataset.ext);
    });
    card.querySelector(".btn-show").onclick = (e) => {
      const ans = card.querySelector(".q-ans");
      ans.classList.toggle("hidden");
      e.target.textContent = ans.classList.contains("hidden") ? "显示答案" : "收起答案";
    };
    box.appendChild(card);
  });
}

// ---------- 聊天 ----------
async function loadMessages() {
  const msgs = await api(`/api/courses/${courseState.currentId}/messages`);
  const log = $("#chat-log");
  log.innerHTML = `<div class="chat-hint">提问会<strong>只在当前课程的资料范围内</strong>检索回答，并标注出处页码。</div>`;
  for (const m of msgs) appendMsg(m.role, m.content, m.citations);
  log.scrollTop = log.scrollHeight;
}

function appendMsg(role, content, citations = []) {
  const log = $("#chat-log");
  const div = document.createElement("div");
  div.className = role === "user" ? "msg msg-user" : "msg msg-ai";
  div.innerHTML = formatAiText(content);
  if (role === "assistant" && citations?.length) div.appendChild(citeRow(citations));
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function formatAiText(text) {
  let html = esc(text);
  html = html.replace(/\[(\d{1,2})\]/g, '<span style="color:var(--accent);font-size:12px">[$1]</span>');
  return html.replace(/\n/g, "<br>");
}

function citeRow(citations) {
  const row = document.createElement("div");
  row.className = "cite-row";
  for (const c of citations) {
    const a = document.createElement("a");
    a.className = "cite";
    a.href = "javascript:void(0)";
    if (c.material_id) a.onclick = () => openViewer(c.material_id, c.page, c.orig_name, c.ext);
    else { a.style.pointerEvents = "none"; a.style.opacity = ".7"; }
    a.textContent = `[${c.n}] ${c.orig_name} · ${unitLabel(c.ext, c.page)}`;
    row.appendChild(a);
  }
  return row;
}

// 「允许外部资料」开关：开启后跨课程检索 + 允许 AI 补充资料外知识；状态记在本地
const EXT_KEY = "sls-allow-external";
const extBox = $("#chat-allow-external");
extBox.checked = storage.get(EXT_KEY) === "1";
$("#ext-switch").classList.toggle("on", extBox.checked);
extBox.onchange = () => {
  storage.set(EXT_KEY, extBox.checked ? "1" : "0");
  $("#ext-switch").classList.toggle("on", extBox.checked);
  toast(extBox.checked
    ? "已开启外部资料：可跨课程检索，资料不足时 AI 会补充并标明"
    : "已关闭：只在当前课程资料范围内回答");
};

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (materialState.busy) return;
  const input = $("#chat-input");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  appendMsg("user", question);
  await runChat({ question, mode: "ask", allow_external: extBox.checked });
});

// ---------- 设置 ----------
$("#btn-settings").onclick = async () => {
  const s = await api("/api/settings");
  $("#set-key").value = "";
  $("#set-threshold").value = s.threshold;
  $("#set-key-state").textContent = s.has_key ? "已配置 API Key（留空则不修改）" : "尚未配置，问答功能不可用";
  openModal("#modal-settings");
};
$("#btn-save-settings").onclick = async () => {
  const body = { threshold: parseFloat($("#set-threshold").value) || 0.42 };
  const key = $("#set-key").value.trim();
  if (key) body.api_key = key;
  await api("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  closeModal("#modal-settings");
  toast("设置已保存");
};


// ---------- 对话执行（依赖 core 的 streamSSE） ----------
async function runChat({ question, mode, allow_external = false }) {
  materialState.busy = true;
  $("#btn-send").disabled = true;
  const log = $("#chat-log");
  const div = document.createElement("div");
  div.className = "msg msg-ai";
  div.innerHTML = `<span class="cursor"></span>`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  let text = "";
  const paint = (withCursor) => {
    div.innerHTML = formatAiText(text) + (withCursor ? `<span class="cursor"></span>` : "");
    log.scrollTop = log.scrollHeight;
  };
  try {
    await streamSSE(`/api/courses/${courseState.currentId}/chat`, { question, mode, allow_external }, {
      onDelta: (d) => { text += d; paint(true); },
      onError: (msg) => { text += `\n\n${msg}`; paint(false); },
      onDone: (citations) => {
        paint(false);
        if (citations.length) div.appendChild(citeRow(citations));
        log.scrollTop = log.scrollHeight;
      },
    });
    if (!text) div.innerHTML = `<span class="muted">（无返回内容）</span>`;
  } catch (err) {
    div.innerHTML = `${esc(err.message)}`;
  } finally {
    materialState.busy = false;
    $("#btn-send").disabled = false;
    log.scrollTop = log.scrollHeight;
  }
}

$("#btn-clear-chat").onclick = async () => {
  if (!confirm("清空当前课程的全部对话记录？")) return;
  await api(`/api/courses/${courseState.currentId}/messages`, { method: "DELETE" });
  loadMessages();
};

// 导学：切到互动学习页并请求 AI 导学
$("#btn-guide").onclick = async () => {
  if (materialState.busy) return;
  switchTab("study");
  appendMsg("user", "请求 AI 导学…");
  await runChat({ question: "", mode: "guide" });
};
