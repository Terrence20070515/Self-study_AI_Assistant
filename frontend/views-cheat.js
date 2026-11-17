/* 速查表：四段（术语/公式/代码/易错点），每条挂页码可跳。
   应用内可编辑 —— 考前一周发现自己老忘某个点，就加一行进去；
   PDF 是终点，可改的页面才是过程。 */

const cheatState = { courseId: null, course: null, items: [], counts: {}, busy: false };

const CHEAT_SECTIONS = [
  ["terms", "术语表"],
  ["formulas", "公式与规则"],
  ["code", "代码模板"],
  ["pitfalls", "易错点"],
];

/* ---------------- 入口 ---------------- */

function openCheat() {
  showView("cheat");
  renderCheatCoursePicker();
  const hasCourse = !!cheatState.courseId;
  // 「换课程」只在已经有课程时才有意义 —— 选课页本身就是在换课程
  $("#cheat-actions").classList.toggle("hidden", !hasCourse);
  if (hasCourse) {
    $("#cheat-pick").classList.add("hidden");
    $("#cheat-panel").classList.remove("hidden");
    loadCheat(cheatState.courseId);
  } else {
    $("#cheat-pick").classList.remove("hidden");
    $("#cheat-panel").classList.add("hidden");
  }
}

async function renderCheatCoursePicker() {
  const box = $("#cheat-course-list");
  if (!courseState.list.length) await loadCourses();
  const list = courseState.list.filter((c) => c.code !== "UNFILED");
  box.innerHTML = "";
  if (!list.length) { box.innerHTML = `<div class="material-empty">还没有课程</div>`; return; }
  for (const c of list) {
    const btn = document.createElement("button");
    btn.className = "kg-course-btn";
    btn.innerHTML = `<b>${esc(c.code)}</b><span>${esc(c.name || "")}</span>`;
    btn.onclick = () => {
      cheatState.courseId = c.id;
      cheatState.course = c;
      $("#cheat-pick").classList.add("hidden");
      $("#cheat-panel").classList.remove("hidden");
      $("#cheat-actions").classList.remove("hidden");
      loadCheat(c.id);
    };
    box.appendChild(btn);
  }
}

async function loadCheat(cid) {
  let data;
  try {
    data = await api(`/api/courses/${cid}/cheat`);
  } catch (e) { return toast(`读取失败：${e.message}`); }
  cheatState.items = data.items || [];
  cheatState.counts = data.counts || {};
  const co = cheatState.course || courseState.list.find((c) => c.id === cid);
  $("#cheat-title").textContent = co ? co.code : "";
  renderCheat();
}

/* ---------------- 渲染 ---------------- */

function cheatItemEl(it, idx) {
  const row = document.createElement("div");
  row.className = "cheat-item";
  row.dataset.id = String(it.id);
  row.dataset.section = it.section;

  const head = document.createElement("div");
  head.className = "cheat-item-head";
  const num = document.createElement("span");
  num.className = "cheat-num";
  num.textContent = String(idx);
  head.appendChild(num);

  const title = document.createElement("div");
  title.className = "cheat-title";
  title.contentEditable = "true";
  title.spellcheck = false;
  title.dataset.field = "title";
  title.textContent = it.title || "";
  if (!it.title) title.dataset.empty = "1";
  head.appendChild(title);
  row.appendChild(head);

  const body = document.createElement("div");
  body.className = "cheat-body-text";
  body.contentEditable = "true";
  body.spellcheck = false;
  body.dataset.field = "body";
  body.textContent = it.body || "";
  if (!it.body) body.dataset.empty = "1";
  row.appendChild(body);

  const foot = document.createElement("div");
  foot.className = "cheat-foot";
  if (it.page) {
    const ref = document.createElement("button");
    ref.className = "cheat-ref";
    ref.textContent = `${it.orig_name || "原文"} · p.${it.page}`;
    ref.onclick = () => openImmersive(
      { id: it.material_id, orig_name: it.orig_name || "", ext: it.ext || "pdf" }, it.page);
    foot.appendChild(ref);
  } else {
    const ph = document.createElement("span");
    ph.className = "cheat-ref muted";
    ph.textContent = "未关联页码";
    foot.appendChild(ph);
  }
  const del = document.createElement("button");
  del.className = "cheat-del";
  del.textContent = "删除";
  del.onclick = async () => {
    if (!confirm("删掉这一条？")) return;
    try {
      await api(`/api/cheat/items/${it.id}`, { method: "DELETE" });
      cheatState.items = cheatState.items.filter((x) => x.id !== it.id);
      renderCheat();
    } catch (e) { toast(`删除失败：${e.message}`); }
  };
  foot.appendChild(del);
  row.appendChild(foot);

  // 就地编辑：失焦即存（比「编辑-保存」少一步，改一个错别字不该走流程）
  for (const el of [title, body]) {
    el.addEventListener("blur", () => saveCheatField(row, el));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); }
    });
  }
  return row;
}

async function saveCheatField(row, el) {
  const id = parseInt(row.dataset.id, 10);
  const field = el.dataset.field;
  const val = el.innerText.replace(/\u00a0/g, " ").trim();
  const it = cheatState.items.find((x) => x.id === id);
  if (!it || (it[field] || "") === val) return;
  try {
    await api(`/api/cheat/items/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: val }),
    });
    it[field] = val;
    el.classList.remove("saving");
  } catch (e) {
    el.classList.add("saving");     // 标记成未保存，避免用户以为改成了
    toast(`保存失败：${e.message}`);
  }
}

function renderCheat() {
  const box = $("#cheat-body");
  box.innerHTML = "";
  // 没内容就没有可导出的东西，按钮直接不出现（不是灰着 —— 灰着会让人去点）
  $("#cheat-pdf").classList.toggle("hidden", cheatState.items.length === 0);
  if (!cheatState.items.length) {
    box.innerHTML = `<div class="material-empty">还没有内容。点「AI 生成」勾几份资料，
      或者「＋ 加一条」自己写。</div>`;
    return;
  }
  for (const [sec, label] of CHEAT_SECTIONS) {
    const rows = cheatState.items.filter((x) => x.section === sec);
    if (!rows.length) continue;
    const block = document.createElement("section");
    block.className = "cheat-sec";
    const head = document.createElement("div");
    head.className = "cheat-sec-head";
    head.innerHTML = `<b>${label}</b><span class="muted">${rows.length} 条</span>
      <button class="btn btn-ghost btn-sm" data-add="${sec}">＋ 加一条</button>`;
    block.appendChild(head);
    head.querySelector("[data-add]").onclick = guard("加一条", () => addCheatItem(sec));
    rows.forEach((it, i) => block.appendChild(cheatItemEl(it, i + 1)));
    box.appendChild(block);
  }
}

/* ---------------- 增删改 ---------------- */

async function addCheatItem(section) {
  const it = await api(`/api/courses/${cheatState.courseId}/cheat/items`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ section, title: "", body: "" }),
  });
  cheatState.items.push(it);
  renderCheat();
  // 新条目直接把光标放进标题里
  const row = document.querySelector(`.cheat-item[data-id="${it.id}"] .cheat-title`);
  if (row) { row.focus(); row.dataset.empty = "1"; }
}

$("#dash-cheat").onclick = guard("打开速查表", openCheat);
$("#cheat-switch").onclick = guard("换课程", () => {
  cheatState.courseId = null;
  cheatState.items = [];
  $("#cheat-panel").classList.add("hidden");
  $("#cheat-pick").classList.remove("hidden");
  $("#cheat-actions").classList.add("hidden");
  renderCheatCoursePicker();
});
$("#cheat-add").onclick = guard("加一条", () => addCheatItem("terms"));

/* ---------------- 生成 ---------------- */

$("#cheat-gen").onclick = guard("生成速查表", async () => {
  if (!cheatState.courseId) return;
  let mats;
  try { mats = await api(`/api/materials/all`); } catch (e) { return toast(e.message); }
  const mine = mats.filter((m) => m.course_id === cheatState.courseId && m.status === "ready");
  const box = $("#cheat-mat-list");
  box.innerHTML = "";
  if (!mine.length) {
    box.innerHTML = `<div class="material-empty">这门课还没有已解析的资料</div>`;
    openModal("#modal-cheat-gen");
    return;
  }
  let saved = [];
  try {
    saved = JSON.parse(storage.get(`cheat-gen-${cheatState.courseId}`) || "[]");
  } catch (e) { saved = []; }
  for (const m of mine) {
    const row = document.createElement("label");
    row.className = "kg-mat-row";
    row.innerHTML = `<input type="checkbox" value="${esc(m.id)}"`
      + (saved.includes(m.id) ? " checked" : "") + `>
      <span>${esc(m.orig_name)}</span>`;
    box.appendChild(row);
  }
  openModal("#modal-cheat-gen");
});

$("#cheat-gen-go").onclick = guard("生成速查表", async () => {
  const ids = [...$("#cheat-mat-list").querySelectorAll("input:checked")].map((i) => i.value);
  if (!ids.length) return toast("先勾选至少一份资料");
  if (cheatState.items.length && !confirm("会覆盖当前速查表的全部内容，继续？")) return;
  storage.set(`cheat-gen-${cheatState.courseId}`, JSON.stringify(ids));
  const btn = $("#cheat-gen-go");
  btn.disabled = true; btn.textContent = "生成中…";
  try {
    const r = await api(`/api/courses/${cheatState.courseId}/cheat/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ material_ids: ids }),
    });
    cheatState.items = r.data.items || [];
    cheatState.counts = r.data.counts || {};
    closeModal("#modal-cheat-gen");
    renderCheat();
    toast(`生成了 ${r.added} 条`);
  } catch (e) {
    toast(`生成失败：${e.message}`);
  } finally {
    btn.disabled = false; btn.textContent = "生成";
  }
});

/* ---------------- 导出 ---------------- */

$("#cheat-pdf").onclick = guard("导出 PDF", async () => {
  if (!cheatState.courseId) return toast("先选课程");
  if (!cheatState.items.length) return toast("速查表还是空的");

  // 桌面窗口是 WKWebView，没有下载代理：必须走原生保存框，
  // 否则 <a download> 点了毫无反应
  if (hasNativeBridge()) {
    try {
      const path = await window.pywebview.api.export_cheat_pdf(cheatState.courseId);
      if (path) toast(`已导出到：${path}`);
      else toast("已取消");
      return;
    } catch (e) { /* 桥不可用就退回浏览器下载 */ }
  }
  try {
    const res = await fetch(`/api/courses/${cheatState.courseId}/cheat.pdf`);
    if (!res.ok) {
      let msg = "导出失败";
      try { msg = (await res.json()).detail || msg; } catch (e) { /* 非 JSON */ }
      return toast(msg);
    }
    const blob = await res.blob();
    const a = document.createElement("a");
    const url = URL.createObjectURL(blob);
    a.href = url;
    a.download = `${(cheatState.course && cheatState.course.code) || "cheat"}-cheatsheet.pdf`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast("已导出 PDF");
  } catch (e) {
    toast(`导出失败：${e.message}`);
  }
});
