/* SQL 训练（SOE101）：题型仿课程那份 CPT103 SQL Revision ——
   三值逻辑求值、概念多选、给表写查询（填空）。
   判分在本地比对，不调模型：选一个 SQL 关键字，确定性比对比语义判断更准也更快。 */

const sqlState = {
  courseId: null,
  tasks: [],
  progress: {},
  currentKey: null,
  picks: new Set(),     // 选择题当前勾选
  busy: false,
};

const SQL_CODES = ["SOE101"];
const SQL_KIND_LABEL = { choice: "选择", table: "算结果", blank: "填空" };

function sqlSupported(course) {
  return SQL_CODES.includes(String((course && course.code) || "").toUpperCase());
}

function syncSqlEntry(course) {
  const btn = document.querySelector("#btn-sql");
  if (btn) btn.classList.toggle("hidden", !sqlSupported(course));
}

function sqlDraftKey(key) {
  return `sls-sql-draft-${sqlState.courseId}-${key}`;
}

async function openSqlTrainPage(courseId) {
  const cid = courseId || courseState.currentId;
  if (!cid) return;
  sqlState.courseId = cid;
  sqlState.currentKey = null;
  showView("sqltrain");
  await loadSqlTasks();
}

async function loadSqlTasks() {
  const box = document.querySelector("#sql-list");
  box.innerHTML = `<div class="asm-list-hint">加载题目…</div>`;
  let r;
  try {
    r = await api(`/api/courses/${sqlState.courseId}/sqltrain/tasks`);
  } catch (e) {
    box.innerHTML = `<div class="asm-list-hint">${esc(e.message)}</div>`;
    return;
  }
  if (!r.supported) {
    box.innerHTML = `<div class="asm-list-hint">这门课还没有 SQL 题库</div>`;
    return;
  }
  sqlState.tasks = r.tasks || [];
  sqlState.progress = r.progress || {};
  renderSqlList();
  const next = sqlState.tasks.find((t) => {
    const p = sqlState.progress[t.key];
    return !p || (p.best || 0) < (p.total || t.total || 1);
  }) || sqlState.tasks[0];
  if (next) selectSqlTask(next.key);
}

function isFull(key) {
  const t = sqlState.tasks.find((x) => x.key === key);
  const p = sqlState.progress[key];
  if (!t || !p) return false;
  return (p.best || 0) >= (t.total || 1);
}

function renderSqlList() {
  const box = document.querySelector("#sql-list");
  if (!box) return;
  box.innerHTML = "";
  const passed = sqlState.tasks.filter((t) => isFull(t.key)).length;

  const head = document.createElement("div");
  head.className = "asm-list-head";
  head.innerHTML = `<span>${sqlState.tasks.length} 道题</span>
    <span class="asm-list-pass">满分 ${passed}</span>`;
  box.appendChild(head);

  sqlState.tasks.forEach((t, i) => {
    const p = sqlState.progress[t.key];
    const best = p ? p.best || 0 : null;
    const total = t.total || 1;
    const el = document.createElement("button");
    el.className = "asm-item" + (t.key === sqlState.currentKey ? " active" : "");
    el.innerHTML =
      `<span class="asm-item-no">${String(i + 1).padStart(2, "0")}</span>
       <span class="asm-item-body">
         <b>${esc(t.title)}</b>
         <em>${esc(t.source)} · ${esc(t.level)} · ${SQL_KIND_LABEL[t.kind] || "填空"}</em>
       </span>
       <span class="asm-item-score${best === null ? "" : (best >= total ? " ok" : " half")}">`
       + `${best === null ? "—" : best + "/" + total}</span>`;
    el.onclick = () => selectSqlTask(t.key);
    box.appendChild(el);
  });
}

function selectSqlTask(key) {
  const t = sqlState.tasks.find((x) => x.key === key);
  if (!t) return;
  sqlState.currentKey = key;
  sqlState.picks = new Set();

  document.querySelector("#sql-title").textContent = t.title;
  document.querySelector("#sql-meta").textContent =
    `${t.level} · ${t.source} · ${SQL_KIND_LABEL[t.kind] || "填空"}`;
  document.querySelector("#sql-brief").textContent = t.brief;
  document.querySelector("#sql-result").innerHTML = "";
  const hint = document.querySelector("#sql-hint-box");
  hint.classList.add("hidden");
  hint.innerHTML = "";

  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(sqlDraftKey(key)) || "null"); } catch (e) { saved = null; }

  if (t.kind === "choice") renderSqlChoice(t, saved);
  else if (t.kind === "table") renderSqlTable(t, saved);
  else renderSqlBlank(t, saved);

  const p = sqlState.progress[key];
  document.querySelector("#sql-score").textContent = p
    ? `最好 ${p.best}/${t.total} · 提交过 ${p.tries} 次`
    : "还没做过";
  renderSqlList();
}

/* ---------------- 选择题 ---------------- */
function renderSqlChoice(t, saved) {
  const box = document.querySelector("#sql-question");
  box.innerHTML = "";
  if (saved && Array.isArray(saved.picks)) sqlState.picks = new Set(saved.picks);

  const stem = document.createElement("pre");
  stem.className = "sql-stem";
  stem.textContent = t.stem;
  box.appendChild(stem);

  const tip = document.createElement("div");
  tip.className = "asm-label";
  tip.innerHTML = t.multi
    ? "可选多项　<span class=\"muted\">选完点「提交检查」；少选或错选都算错</span>"
    : "单选　<span class=\"muted\">选完点「提交检查」</span>";
  box.appendChild(tip);

  box.appendChild(buildSqlOptions(t));
}

/* 选项列表（选择题与算结果题共用） */
function buildSqlOptions(t) {
  const list = document.createElement("div");
  list.className = "sql-opts";
  t.options.forEach((txt, i) => {
    const L = String.fromCharCode(65 + i);
    const el = document.createElement("button");
    el.className = "sql-opt" + (sqlState.picks.has(L) ? " picked" : "");
    el.dataset.letter = L;
    el.innerHTML = `<i>${L}</i><span>${esc(txt)}</span>`;
    el.onclick = () => {
      if (!t.multi) sqlState.picks.clear();
      if (sqlState.picks.has(L)) sqlState.picks.delete(L);
      else sqlState.picks.add(L);
      list.querySelectorAll(".sql-opt").forEach((b) =>
        b.classList.toggle("picked", sqlState.picks.has(b.dataset.letter)));
      saveSqlDraft();
    };
    list.appendChild(el);
  });
  return list;
}

/* ---------------- 给表算结果 ---------------- */
function renderSqlTable(t, saved) {
  const box = document.querySelector("#sql-question");
  box.innerHTML = "";
  if (saved && Array.isArray(saved.picks)) sqlState.picks = new Set(saved.picks);

  // 表：(name) + 表头 + 数据行；NULL 单独上色
  const tables = document.createElement("div");
  tables.className = "sql-tables";
  (t.tables || []).forEach((tb) => {
    const wrap = document.createElement("div");
    wrap.className = "sql-table-wrap";
    const cap = document.createElement("div");
    cap.className = "sql-table-cap";
    cap.textContent = tb.name;
    wrap.appendChild(cap);
    const table = document.createElement("table");
    table.className = "sql-table";
    const thead = document.createElement("thead");
    const hr = document.createElement("tr");
    (tb.columns || []).forEach((c) => {
      const th = document.createElement("th");
      th.textContent = c;
      hr.appendChild(th);
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    (tb.rows || []).forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((v) => {
        const td = document.createElement("td");
        if (v === null || v === undefined) {
          td.textContent = "NULL";
          td.className = "sql-null";
        } else {
          td.textContent = String(v);
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    tables.appendChild(wrap);
  });
  box.appendChild(tables);

  const label = document.createElement("div");
  label.className = "asm-label";
  label.textContent = "查询";
  box.appendChild(label);
  const q = document.createElement("pre");
  q.className = "sql-stem sql-query";
  q.textContent = t.query;
  box.appendChild(q);

  const ask = document.createElement("div");
  ask.className = "sql-ask";
  ask.innerHTML = fmtAsk(t.question);
  box.appendChild(ask);

  const tip = document.createElement("div");
  tip.className = "asm-label";
  tip.innerHTML = t.multi
    ? "可选多项　<span class=\"muted\">选完点「提交检查」；少选或错选都算错</span>"
    : "单选　<span class=\"muted\">选完点「提交检查」</span>";
  box.appendChild(tip);

  box.appendChild(buildSqlOptions(t));
}

/* 题干里的 **加粗** 转成 <b>，其余转义 */
function fmtAsk(text) {
  return esc(String(text || "")).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
}

/* ---------------- 填空题 ---------------- */
function renderSqlBlank(t, saved) {
  const box = document.querySelector("#sql-question");
  box.innerHTML = "";

  const label = document.createElement("div");
  label.className = "asm-label";
  label.innerHTML = `填空　<span class="muted">把每一处 ____ 换成正确的内容；Enter 跳到下一个空</span>`;
  box.appendChild(label);

  const wrap = document.createElement("div");
  wrap.className = "asm-code";
  let idx = 0;
  const values = (saved && saved.answers) || [];

  t.parts.forEach((part) => {
    if (part.label) {
      const lab = document.createElement("div");
      lab.className = "asm-part";
      lab.textContent = part.label;
      wrap.appendChild(lab);
    }
    (part.lines || []).forEach((line, i) => {
      const row = document.createElement("div");
      row.className = "asm-line";
      const num = document.createElement("span");
      num.className = "asm-ln";
      num.textContent = i + 1;
      row.appendChild(num);

      const code = document.createElement("span");
      code.className = "asm-code-line";
      const segs = String(line).split("____");
      segs.forEach((seg, k) => {
        if (seg) code.appendChild(document.createTextNode(seg));
        if (k < segs.length - 1) {
          const inp = document.createElement("input");
          inp.className = "asm-blank";
          inp.dataset.idx = String(idx);
          inp.spellcheck = false;
          inp.autocomplete = "off";
          inp.value = values[idx] || "";
          inp.addEventListener("input", saveSqlDraft);
          inp.addEventListener("keydown", (e) => {
            if (e.key !== "Enter") return;
            e.preventDefault();
            const all = [...wrap.querySelectorAll(".asm-blank")];
            const at = all.indexOf(inp);
            if (at >= 0 && at < all.length - 1) all[at + 1].focus();
            else checkSql();
          });
          code.appendChild(inp);
          idx += 1;
        }
      });
      row.appendChild(code);
      wrap.appendChild(row);
    });
  });
  box.appendChild(wrap);
  const first = wrap.querySelector(".asm-blank");
  if (first && !values.length) setTimeout(() => first.focus(), 60);
}

function blankInputs() {
  return [...document.querySelectorAll("#sql-question .asm-blank")];
}

function saveSqlDraft() {
  if (!sqlState.currentKey) return;
  const t = sqlState.tasks.find((x) => x.key === sqlState.currentKey);
  if (!t) return;
  const payload = t.kind === "choice"
    ? { picks: [...sqlState.picks] }
    : { answers: blankInputs().map((i) => i.value) };
  try { localStorage.setItem(sqlDraftKey(sqlState.currentKey), JSON.stringify(payload)); } catch (e) { /* 存不下就算了 */ }
}

/* ---------------- 判分 ---------------- */
async function checkSql() {
  if (sqlState.busy || !sqlState.currentKey) return;
  const t = sqlState.tasks.find((x) => x.key === sqlState.currentKey);
  if (!t) return;

  let body;
  if (t.kind === "choice" || t.kind === "table") {
    if (!sqlState.picks.size) return toast("先选一个再检查");
    body = { task_key: t.key, picks: [...sqlState.picks] };
  } else {
    const answers = blankInputs().map((i) => i.value);
    if (!answers.some((a) => a.trim())) return toast("先填几个空再检查");
    body = { task_key: t.key, answers };
  }

  const btn = document.querySelector("#btn-sql-check");
  const box = document.querySelector("#sql-result");
  sqlState.busy = true;
  btn.disabled = true;
  btn.textContent = "检查中…";
  box.innerHTML = `<div class="asm-empty">正在核对…</div>`;
  let r;
  try {
    r = await api(`/api/courses/${sqlState.courseId}/sqltrain/check`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    box.innerHTML = `<div class="asm-empty">${esc(e.message)}</div>`;
    sqlState.busy = false;
    btn.disabled = false;
    btn.textContent = "提交检查";
    return;
  }
  renderSqlResult(r, t);

  const prev = sqlState.progress[t.key] || { best: 0, tries: 0 };
  sqlState.progress[t.key] = {
    best: Math.max(prev.best || 0, r.score || 0),
    total: r.total,
    tries: (prev.tries || 0) + 1,
  };
  document.querySelector("#sql-score").textContent =
    `最好 ${sqlState.progress[t.key].best}/${r.total} · 提交过 ${sqlState.progress[t.key].tries} 次`;
  renderSqlList();

  sqlState.busy = false;
  btn.disabled = false;
  btn.textContent = "提交检查";
}

function renderSqlResult(r, t) {
  const box = document.querySelector("#sql-result");
  box.innerHTML = "";
  const head = document.createElement("div");
  head.className = "sql-sum " + (r.score === r.total ? "ok" : (r.score ? "half" : "bad"));
  head.innerHTML = r.score === r.total
    ? `<b>全对</b> · ${r.score}/${r.total}`
    : `<b>${r.score}/${r.total}</b>`;
  box.appendChild(head);

  if (r.kind === "choice" || r.kind === "table") {
    const list = document.querySelector("#sql-question .sql-opts");
    (r.options || []).forEach((o) => {
      const el = list && list.querySelector(`.sql-opt[data-letter="${o.letter}"]`);
      if (!el) return;
      el.classList.add("locked");
      el.onclick = null;
      el.classList.remove("picked");
      if (o.correct) el.classList.add("right");
      else if (o.picked) el.classList.add("wrong");
      el.classList.add(o.picked ? "picked" : "unpicked");
    });
    const line = document.createElement("div");
    line.className = "sql-verdict";
    line.innerHTML = `你选了 <b>${(r.picked || []).join(" ") || "（空）"}</b>　`
      + `正确答案 <b>${(r.answer || []).join(" ")}</b>`;
    box.appendChild(line);
  } else {
    (r.blanks || []).forEach((b, i) => {
      const inp = document.querySelector(`#sql-question .asm-blank[data-idx="${i}"]`);
      if (inp) {
        inp.classList.remove("ok", "bad", "near");
        inp.classList.add(b.ok ? "ok" : "bad");
        inp.disabled = false;
      }
      const row = document.createElement("div");
      row.className = "sql-blank-row " + (b.ok ? "ok" : "bad");
      row.innerHTML = `<b>第 ${i + 1} 空</b>`
        + (b.ok ? `<span>填对了：${esc(b.yours)}</span>`
                : `<span>你填：<em>${esc(b.yours || "（空）")}</em>　应为：<b>${esc(b.answer)}</b></span>`
                  + (b.why ? `<div class="sql-why">${esc(b.why)}</div>` : ""));
      box.appendChild(row);
    });
  }

  const explain = r.note || r.why;
  if (explain) {
    const note = document.createElement("div");
    note.className = "sql-note";
    note.innerHTML = `<b>要点</b>　${esc(explain)}`;
    box.appendChild(note);
  }
}

/* ---------------- 事件 ---------------- */
document.querySelector("#btn-sql").onclick = guard("打开 SQL 训练", () => openSqlTrainPage(courseState.currentId));
document.querySelector("#btn-sql-back").onclick = guard("返回互动学习", () => openCourseChat(sqlState.courseId || courseState.currentId));
document.querySelector("#btn-sql-check").onclick = guard("提交检查", checkSql);

document.querySelector("#btn-sql-hint").onclick = () => {
  const t = sqlState.tasks.find((x) => x.key === sqlState.currentKey);
  if (!t) return;
  const box = document.querySelector("#sql-hint-box");
  const open = box.classList.toggle("hidden") === false;
  if (open && !box.innerHTML) {
    box.innerHTML = t.kind === "choice"
      ? `<div class="asm-label">提示</div><div>${esc(t.brief)}</div>`
      : `<div class="asm-label">提示（只给方向，不直接给答案）</div>`
        + `<ol>${(t.blanks || []).map((b, i) =>
            `<li><b>第 ${i + 1} 空</b>：${esc(b.hint || "")}</li>`).join("")}</ol>`;
  }
  if (open) box.scrollIntoView({ block: "nearest", behavior: "smooth" });
};

document.querySelector("#btn-sql-clear").onclick = () => {
  if (sqlState.currentKey) {
    try { localStorage.removeItem(sqlDraftKey(sqlState.currentKey)); } catch (e) { /* ignore */ }
  }
  const t = sqlState.tasks.find((x) => x.key === sqlState.currentKey);
  if (!t) return;
  sqlState.picks = new Set();
  document.querySelector("#sql-result").innerHTML = "";
  if (t.kind === "choice") renderSqlChoice(t, null);
  else if (t.kind === "table") renderSqlTable(t, null);
  else renderSqlBlank(t, null);
};
