/* 知识图：每门课一张可长期维护的概念图。
   节点 = 知识点，点一下跳原文那一页；连线自由，但必须带类型（属于/依赖/对比）。
   不显示任何进度、正确率、页码统计 —— 那些对复习没有决策价值。 */

const mapState = {
  courseId: null,
  course: null,
  nodes: [],
  edges: [],
  sel: null,          // 选中的节点 id
  linkKind: null,     // 连线模式：null | belongs | depends | contrast
  linkFrom: null,     // 连线模式下点中的第一个节点
  dragging: null,
  editing: null,      // 正在编辑文字的节点 id
};

const KG_KIND_LABEL = { belongs: "属于", depends: "依赖", contrast: "对比" };
const KG_NODE_W = 190, KG_NODE_H = 44;

/* ---------------- 入口 ---------------- */

function openMap() {
  showView("map");
  renderMapCoursePicker();
  // 「换课程」只在已选课程时出现：没选课时这个按钮等于让你回到现在这一页
  $("#kg-switch").classList.toggle("hidden", !mapState.courseId);
  if (mapState.courseId) {
    $("#kg-pick").classList.add("hidden");
    $("#kg-panel").classList.remove("hidden");
    loadMap(mapState.courseId);
  } else {
    $("#kg-pick").classList.remove("hidden");
    $("#kg-panel").classList.add("hidden");
  }
}

async function renderMapCoursePicker() {
  const box = $("#kg-course-list");
  if (!courseState.list.length) await loadCourses();
  const list = courseState.list.filter((c) => c.code !== "UNFILED");
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<div class="material-empty">还没有课程</div>`;
    return;
  }
  for (const c of list) {
    const btn = document.createElement("button");
    btn.className = "kg-course-btn";
    btn.innerHTML = `<b>${esc(c.code)}</b><span>${esc(c.name || "")}</span>`;
    btn.onclick = () => {
      mapState.courseId = c.id;
      mapState.course = c;
      $("#kg-pick").classList.add("hidden");
      $("#kg-panel").classList.remove("hidden");
      $("#kg-switch").classList.remove("hidden");
      loadMap(c.id);
    };
    box.appendChild(btn);
  }
}

async function loadMap(cid) {
  let data;
  try {
    data = await api(`/api/courses/${cid}/map`);
  } catch (e) {
    toast(`读取失败：${e.message}`);
    return;
  }
  mapState.nodes = data.nodes || [];
  mapState.edges = data.edges || [];
  mapState.sel = null;
  mapState.linkKind = null;
  mapState.linkFrom = null;
  const co = mapState.course || courseState.list.find((c) => c.id === cid);
  $("#kg-title").textContent = co ? co.code : "";
  renderMap();
}

/* ---------------- 渲染 ---------------- */

function kgNodeW(n) {
  // 长文字给宽一点的框，避免全挤成两三行
  const len = (n.label || "").length;
  return len > 18 ? KG_NODE_W + 40 : (len > 10 ? KG_NODE_W : KG_NODE_W - 30);
}

function renderMap() {
  const svg = $("#kg-svg");
  const nodes = mapState.nodes;
  $("#kg-empty").classList.toggle("hidden", nodes.length > 0);
  if (!nodes.length) {
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "320");
    svg.innerHTML = "";
    return;
  }

  // 画布尺寸 = 内容包围盒 + 边距；靠外层容器滚动，不做缩放变换
  let maxX = 0, maxY = 0, minX = 0;
  for (const n of nodes) {
    maxX = Math.max(maxX, n.x + kgNodeW(n) / 2);
    maxY = Math.max(maxY, n.y);
    minX = Math.min(minX, n.x - kgNodeW(n) / 2);
  }
  const padX = 80, padY = 90;
  const w = Math.max(900, maxX - minX + padX * 2);
  const h = Math.max(360, maxY + padY * 2);
  const shift = -minX + padX;          // 让最左边的节点也留出边距

  svg.setAttribute("width", String(w));
  svg.setAttribute("height", String(h));
  svg.dataset.shift = String(shift);      // 拖动时要按同一个位移换算，别各算各的
  svg.innerHTML = "";

  const gEdges = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const gNodes = document.createElementNS("http://www.w3.org/2000/svg", "g");
  svg.appendChild(gEdges);
  svg.appendChild(gNodes);

  const byId = new Map(nodes.map((n) => [n.id, n]));
  for (const e of mapState.edges) {
    const a = byId.get(e.from_id), b = byId.get(e.to_id);
    if (!a || !b) continue;
    gEdges.appendChild(kgEdgeEl(a, b, e, shift));
  }
  for (const n of nodes) gNodes.appendChild(kgNodeEl(n, shift));
}

function kgEdgePath(a, b, shift) {
  const x1 = a.x + shift, x2 = b.x + shift;
  const y1 = a.y, y2 = b.y;
  // 从源节点底部 → 目标节点顶部，竖向二次贝塞尔，层级图看起来最顺
  const y1b = y1 + KG_NODE_H / 2, y2t = y2 - KG_NODE_H / 2;
  const mid = (y1b + y2t) / 2;
  return `M ${x1} ${y1b} C ${x1} ${mid}, ${x2} ${mid}, ${x2} ${y2t}`;
}

function kgEdgeEl(a, b, e, shift) {
  const wrap = document.createElementNS("http://www.w3.org/2000/svg", "g");
  wrap.setAttribute("class", `kg-edge kg-edge-${e.kind}`);
  const d = kgEdgePath(a, b, shift);

  const hit = document.createElementNS("http://www.w3.org/2000/svg", "path");
  hit.setAttribute("d", d);
  hit.setAttribute("class", "kg-edge-hit");
  hit.addEventListener("click", (ev) => {
    ev.stopPropagation();
    if (!confirm(`删除这条「${KG_KIND_LABEL[e.kind] || e.kind}」连线？`)) return;
    api(`/api/map/edges/${e.id}`, { method: "DELETE" })
      .then(() => { mapState.edges = mapState.edges.filter((x) => x.id !== e.id); renderMap(); })
      .catch((err) => toast(`删除失败：${err.message}`));
  });
  wrap.appendChild(hit);

  const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
  line.setAttribute("d", d);
  line.setAttribute("class", "kg-edge-line");
  wrap.appendChild(line);

  const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
  const mx = (a.x + b.x) / 2 + shift;
  const my = (a.y + b.y) / 2;
  label.setAttribute("x", String(mx));
  label.setAttribute("y", String(my));
  label.setAttribute("class", "kg-edge-label");
  label.textContent = KG_KIND_LABEL[e.kind] || e.kind;
  wrap.appendChild(label);
  return wrap;
}

function kgNodeEl(n, shift) {
  const w = kgNodeW(n), h = KG_NODE_H;
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("class", "kg-node" + (mapState.sel === n.id ? " sel" : "")
    + (mapState.linkFrom === n.id ? " linking" : ""));
  g.setAttribute("data-id", String(n.id));
  g.setAttribute("transform", `translate(${n.x + shift}, ${n.y})`);

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", String(-w / 2));
  rect.setAttribute("y", String(-h / 2));
  rect.setAttribute("width", String(w));
  rect.setAttribute("height", String(h));
  rect.setAttribute("rx", "9");
  rect.setAttribute("class", "kg-node-box");
  g.appendChild(rect);

  // 用 foreignObject 让文字自动换行（SVG <text> 不会折行）
  const fo = document.createElementNS("http://www.w3.org/2000/svg", "foreignObject");
  fo.setAttribute("x", String(-w / 2 + 8));
  fo.setAttribute("y", String(-h / 2 + 5));
  fo.setAttribute("width", String(w - 16));
  fo.setAttribute("height", String(h - 10));
  const div = document.createElement("div");
  div.className = "kg-label";
  div.textContent = n.label || "（空）";
  fo.appendChild(div);
  g.appendChild(fo);

  if (n.material_id && n.page) {
    const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
    // 放右下角：中间永远是标题文字，右上角容易和长标题打架
    badge.setAttribute("x", String(w / 2 - 6));
    badge.setAttribute("y", String(h / 2 - 5));
    badge.setAttribute("text-anchor", "end");
    badge.setAttribute("class", "kg-page-badge");
    badge.textContent = `p.${n.page}`;
    g.appendChild(badge);
  }

  g.addEventListener("pointerdown", (ev) => kgPointerDown(ev, n, g));
  g.addEventListener("dblclick", (ev) => { ev.stopPropagation(); startEditLabel(n.id); });
  return g;
}

/* ---------------- 交互：拖动 / 选中 / 连线 ---------------- */

function kgPointerDown(ev, n, gEl) {
  if (mapState.editing) return;
  ev.stopPropagation();
  // 连线模式：点两下选两个节点
  if (mapState.linkKind) {
    if (mapState.linkFrom === null) {
      mapState.linkFrom = n.id;
      flashHint(`再点一个节点，画出「${KG_KIND_LABEL[mapState.linkKind]}」连线`);
      renderMap();
      return;
    }
    if (mapState.linkFrom === n.id) { mapState.linkFrom = null; renderMap(); return; }
    const from = mapState.linkFrom, kind = mapState.linkKind;
    mapState.linkFrom = null;
    api(`/api/courses/${mapState.courseId}/map/edges`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_id: from, to_id: n.id, kind }),
    }).then((r) => {
      if (!r.duplicate && r.id) mapState.edges.push(r);
      renderMap();
    }).catch((err) => toast(`连线失败：${err.message}`));
    return;
  }

  mapState.sel = n.id;
  renderMapSelTools();
  renderMap();

  // 拖动
  const svg = $("#kg-svg");
  const start = { x: ev.clientX, y: ev.clientY, nx: n.x, ny: n.y };
  let moved = false;
  const gNode = svg.querySelector(`.kg-node[data-id="${n.id}"]`);
  const target = gNode || gEl;

  const onMove = (e) => {
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    if (!moved && Math.abs(dx) + Math.abs(dy) < 4) return;
    moved = true;
    n.x = Math.round(start.nx + dx);
    n.y = Math.max(30, Math.round(start.ny + dy));
    const shift = Number(svg.dataset.shift || 0);
    target.setAttribute("transform", `translate(${n.x + shift}, ${n.y})`);
  };
  const onUp = () => {
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    if (!moved) return;
    // 拖完重排：连线要跟着走，画布尺寸也可能变
    api(`/api/map/nodes/${n.id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: n.x, y: n.y }),
    }).catch(() => {});
    renderMap();
  };
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
}

function renderMapSelTools() {
  const n = mapState.nodes.find((x) => x.id === mapState.sel);
  const bar = $("#kg-tools");
  if (!n) { bar.classList.add("hidden"); return; }
  bar.classList.remove("hidden");
  $("#kg-sel-label").textContent = n.label || "（空）";
  const go = $("#kg-goto");
  go.classList.toggle("hidden", !(n.material_id && n.page));
  go.textContent = n.page ? `去原文 p.${n.page}` : "去原文";
}

/* ---------------- 编辑文字 ---------------- */

function startEditLabel(nid) {
  const n = mapState.nodes.find((x) => x.id === nid);
  if (!n) return;
  mapState.editing = nid;
  const svg = $("#kg-svg");
  const shift = Number(svg.dataset.shift || 0);
  const g = svg.querySelector(`.kg-node[data-id="${nid}"]`);
  if (!g) return;
  const fo = g.querySelector("foreignObject");
  fo.innerHTML = "";
  const input = document.createElement("input");
  input.className = "kg-label-input";
  input.value = n.label || "";
  fo.appendChild(input);
  input.focus();
  input.select();

  let done = false;
  const finish = async (save) => {
    if (done) return;
    done = true;
    mapState.editing = null;
    const val = input.value.trim().slice(0, 80);
    if (save && val && val !== n.label) {
      try {
        await api(`/api/map/nodes/${nid}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ label: val }),
        });
        n.label = val;
      } catch (e) {
        toast(`保存失败：${e.message}`);
      }
    }
    renderMap();
    renderMapSelTools();     // 工具条上的名字要跟着改
  };
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); finish(true); }
    if (e.key === "Escape") { e.preventDefault(); finish(false); }
  });
  input.addEventListener("blur", () => finish(true));
}

/* ---------------- 节点 / 连线的增删 ---------------- */

async function kgAddNode(parentId = 0, preset = {}) {
  const src = mapState.nodes.find((n) => n.id === parentId);
  const node = await api(`/api/courses/${mapState.courseId}/map/nodes`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      label: preset.label || "新知识点",
      material_id: preset.material_id || (src ? src.material_id : ""),
      page: preset.page || (src ? src.page : 0),
      parent_id: parentId || 0,
      x: src ? src.x : 60,
      y: src ? src.y + 90 : 80,
    }),
  });
  mapState.nodes.push(node);
  mapState.sel = node.id;
  renderMapSelTools();
  renderMap();
  // 父子关系落成一条「属于」连线：图上画出来的线必须都能点掉，
  // 隐式父子线既删不掉也说不清
  if (parentId) {
    try {
      const e = await api(`/api/courses/${mapState.courseId}/map/edges`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_id: parentId, to_id: node.id, kind: "belongs" }),
      });
      if (e && e.id && !e.duplicate) mapState.edges.push(e);
    } catch (err) { /* 连线失败不影响节点本身 */ }
  }
  renderMap();
  startEditLabel(node.id);
}

function kgDeleteSelected() {
  const n = mapState.nodes.find((x) => x.id === mapState.sel);
  if (!n) return;
  const kids = mapState.nodes.filter((x) => x.parent_id === n.id).length;
  const msg = kids ? `「${n.label}」下面还有 ${kids} 个子节点，会一起删掉。确定？` : `删除「${n.label}」？`;
  if (!confirm(msg)) return;
  api(`/api/map/nodes/${n.id}`, { method: "DELETE" })
    .then(async () => {
      mapState.sel = null;
      await loadMapKeepCourse();
    })
    .catch((e) => toast(`删除失败：${e.message}`));
}

async function loadMapKeepCourse() {
  const data = await api(`/api/courses/${mapState.courseId}/map`);
  mapState.nodes = data.nodes || [];
  mapState.edges = data.edges || [];
  renderMapSelTools();
  renderMap();
}

/* ---------------- 工具条 ---------------- */

function flashHint(text, ms = 4000) {
  const el = $("#kg-hint");
  if (!text) { el.classList.add("hidden"); el.textContent = ""; return; }
  el.classList.remove("hidden");
  el.textContent = text;
  clearTimeout(flashHint._t);
  flashHint._t = setTimeout(() => { el.classList.add("hidden"); el.textContent = ""; }, ms);
}

$("#dash-map").onclick = guard("打开知识图", openMap);
$("#kg-back").onclick = () => showHome();
$("#kg-switch").onclick = guard("换课程", () => {
  mapState.courseId = null;
  $("#kg-panel").classList.add("hidden");
  $("#kg-pick").classList.remove("hidden");
  $("#kg-switch").classList.add("hidden");
  renderMapCoursePicker();
});

$("#kg-add-node").onclick = guard("加节点", () => kgAddNode(0));
$("#kg-add-child").onclick = guard("加子节点", () => {
  if (!mapState.sel) return toast("先点一个节点");
  kgAddNode(mapState.sel);
});
$("#kg-edit-label").onclick = guard("改文字", () => {
  if (!mapState.sel) return toast("先点一个节点");
  startEditLabel(mapState.sel);
});
$("#kg-goto").onclick = guard("去原文", () => {
  const n = mapState.nodes.find((x) => x.id === mapState.sel);
  if (!n || !n.material_id) return;
  openImmersive({ id: n.material_id, orig_name: "", ext: "pdf" }, n.page || 1);
});
$("#kg-del-node").onclick = guard("删除节点", kgDeleteSelected);

for (const btn of document.querySelectorAll("#kg-kinds [data-kind]")) {
  btn.onclick = guard("连线模式", () => {
    const kind = btn.dataset.kind;
    if (mapState.linkKind === kind) {          // 再点一次退出
      mapState.linkKind = null;
      mapState.linkFrom = null;
      flashHint("");
    } else {
      mapState.linkKind = kind;
      mapState.linkFrom = null;
      flashHint(`点两个节点，画出「${KG_KIND_LABEL[kind]}」连线（Esc 取消）`);
    }
    document.querySelectorAll("#kg-kinds [data-kind]").forEach((b) =>
      b.classList.toggle("btn-primary", b.dataset.kind === mapState.linkKind));
    renderMap();
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (mapState.linkKind) {
    mapState.linkKind = null; mapState.linkFrom = null; flashHint("");
    document.querySelectorAll("#kg-kinds [data-kind]").forEach((b) => b.classList.remove("btn-primary"));
    renderMap();
  }
});

/* ---------------- AI 起草原图 ---------------- */

$("#kg-draft").onclick = guard("起草原图", async () => {
  if (!mapState.courseId) return;
  let mats;
  try { mats = await api(`/api/materials/all`); } catch (e) { return toast(e.message); }
  const mine = mats.filter((m) => m.course_id === mapState.courseId && m.status === "ready");
  const box = $("#kg-mat-list");
  box.innerHTML = "";
  if (!mine.length) {
    box.innerHTML = `<div class="material-empty">这门课还没有已解析的资料</div>`;
    openModal("#modal-kg-draft");
    return;
  }
  // 记住上次勾了哪几份：下次进来不用重挑
  let saved = [];
  try { saved = JSON.parse(storage.get(`kg-draft-${mapState.courseId}`) || "[]"); } catch (e) { saved = []; }
  for (const m of mine) {
    const row = document.createElement("label");
    row.className = "kg-mat-row";
    row.innerHTML = `<input type="checkbox" value="${esc(m.id)}"`
      + (saved.includes(m.id) ? " checked" : "") + `>
      <span>${esc(m.orig_name)}</span>`;
    box.appendChild(row);
  }
  openModal("#modal-kg-draft");
});

$("#kg-draft-go").onclick = guard("生成原图", async () => {
  const box = $("#kg-mat-list");
  const ids = [...box.querySelectorAll("input:checked")].map((i) => i.value);
  if (!ids.length) return toast("先勾选至少一份资料");
  storage.set(`kg-draft-${mapState.courseId}`, JSON.stringify(ids));
  const btn = $("#kg-draft-go");
  btn.disabled = true; btn.textContent = "生成中…";
  try {
    const r = await api(`/api/courses/${mapState.courseId}/map/draft`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ material_ids: ids }),
    });
    mapState.nodes = r.map.nodes || [];
    mapState.edges = r.map.edges || [];
    closeModal("#modal-kg-draft");
    renderMap();
    toast(`已加入 ${r.added} 个节点`);
  } catch (e) {
    toast(`生成失败：${e.message}`);
  } finally {
    btn.disabled = false; btn.textContent = "生成";
  }
});
