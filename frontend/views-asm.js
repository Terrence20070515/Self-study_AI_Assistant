/* 汇编训练：手打 x86 内联汇编 → AI 逐条批改。
   入口在「互动学习」页底部的快捷卡片里，只对 CSI101 / CPT101 显示。
   题目本身在后端 asm_tasks.py，前端不重复维护内容。 */

const ASM_CODES = ["CSI101", "CPT101"];
const asmState = {
  courseId: null,
  tasks: [],
  progress: {},
  currentKey: null,
  busy: false,
};

function asmSupported(course) {
  return ASM_CODES.includes(String((course && course.code) || "").toUpperCase());
}

// openCourse 里调用：这门课有没有汇编题库，决定卡片显不显示
function syncAsmEntry(course) {
  const btn = document.querySelector("#btn-asm");
  if (btn) btn.classList.toggle("hidden", !asmSupported(course));
}

function asmDraftKey(key) {
  return `sls-asm-draft-${asmState.courseId}-${key}`;
}

async function openAsmPage(courseId) {
  const cid = courseId || courseState.currentId;
  if (!cid) return;
  asmState.courseId = cid;
  asmState.currentKey = null;
  showView("asm");
  await loadAsmTasks();
}

async function loadAsmTasks() {
  const box = document.querySelector("#asm-list");
  box.innerHTML = `<div class="asm-list-hint">加载题目…</div>`;
  let r;
  try {
    r = await api(`/api/courses/${asmState.courseId}/asm/tasks`);
  } catch (e) {
    box.innerHTML = `<div class="asm-list-hint">${esc(e.message)}</div>`;
    return;
  }
  if (!r.supported) {
    box.innerHTML = `<div class="asm-list-hint">这门课还没有汇编题库</div>`;
    return;
  }
  asmState.tasks = r.tasks || [];
  asmState.progress = r.progress || {};
  renderAsmList();
  // 默认落到第一道还没达标的题，没有就从头开始
  const next = asmState.tasks.find(t => (asmState.progress[t.key] || {}).best < 7) || asmState.tasks[0];
  if (next) selectAsmTask(next.key);
}

function renderAsmList() {
  const box = document.querySelector("#asm-list");
  if (!box) return;
  box.innerHTML = "";
  const passed = Object.values(asmState.progress).filter(p => (p.best || 0) >= 7).length;

  const head = document.createElement("div");
  head.className = "asm-list-head";
  head.innerHTML = `<span>${asmState.tasks.length} 道题</span>
    <span class="asm-list-pass">达标 ${passed}</span>`;
  box.appendChild(head);

  asmState.tasks.forEach((t, i) => {
    const p = asmState.progress[t.key];
    const best = p ? p.best || 0 : null;
    const el = document.createElement("button");
    el.className = "asm-item" + (t.key === asmState.currentKey ? " active" : "");
    el.innerHTML =
      `<span class="asm-item-no">${String(i + 1).padStart(2, "0")}</span>
       <span class="asm-item-body">
         <b>${esc(t.title)}</b>
         <em>${esc(t.lab)} · ${esc(t.level)}</em>
       </span>
       <span class="asm-item-score${best === null ? "" : (best >= 7 ? " ok" : " half")}">`
       + `${best === null ? "—" : best + "/10"}</span>`;
    el.onclick = () => selectAsmTask(t.key);
    box.appendChild(el);
  });
}

function selectAsmTask(key) {
  const t = asmState.tasks.find(x => x.key === key);
  if (!t) return;
  asmState.currentKey = key;
  document.querySelector("#asm-title").textContent = t.title;
  document.querySelector("#asm-meta").textContent = `${t.level} · ${t.lab}`;
  document.querySelector("#asm-brief").textContent = t.brief;
  document.querySelector("#asm-decls").textContent = t.decls;

  // 有草稿就接着改，没有就用骨架
  const draft = localStorage.getItem(asmDraftKey(key));
  document.querySelector("#asm-code").value = draft !== null ? draft : t.starter;

  const hint = document.querySelector("#asm-hint-box");
  hint.classList.add("hidden");
  hint.innerHTML = "";
  const ref = document.querySelector("#asm-ref-box");
  ref.classList.add("hidden");
  ref.textContent = "";
  document.querySelector("#asm-feedback").innerHTML = "";

  const p = asmState.progress[key];
  document.querySelector("#asm-score").textContent =
    p ? `最好 ${p.best}/10 · 提交过 ${p.tries} 次` : "还没提交过";
  renderAsmList();
}

function renderAsmFeedback(res) {
  const fb = document.querySelector("#asm-feedback");
  const score = res.score || 0;
  const band = score >= 7 ? "ok" : (score >= 4 ? "half" : "bad");

  const items = (res.items || []).map(it =>
    `<li class="${it.pass ? "pass" : "fail"}">
       <span class="asm-check">${it.pass ? "✓" : "✗"}</span>
       <span><b>${esc(it.point)}</b>${it.note ? `<em>${esc(it.note)}</em>` : ""}</span>
     </li>`).join("");

  const errors = (res.errors || []).map(e =>
    `<div class="asm-err">
       ${e.code ? `<code>${esc(e.code)}</code>` : ""}
       <div class="asm-err-issue">${esc(e.issue)}</div>
       ${e.fix ? `<div class="asm-err-fix">改法：${esc(e.fix)}</div>` : ""}
     </div>`).join("");

  fb.innerHTML =
    `<div class="asm-score-row">
       <span class="asm-big ${band}">${score}<i>/10</i></span>
       <span class="asm-verdict">${esc(res.verdict || "")}</span>
     </div>`
    + (items ? `<ul class="asm-checks">${items}</ul>` : "")
    + (errors ? `<div class="asm-errs"><div class="asm-label">要改的地方</div>${errors}</div>` : "")
    + (res.explain ? `<div class="asm-explain"><div class="asm-label">机制</div><p>${esc(res.explain)}</p></div>` : "")
    + (res.next ? `<div class="asm-next">下一步：${esc(res.next)}</div>` : "");
}

// ---------- 事件 ----------
document.querySelector("#btn-asm").onclick = guard("打开汇编训练", () => openAsmPage(courseState.currentId));
document.querySelector("#btn-asm-back").onclick = guard("返回互动学习", () => openCourseChat(asmState.courseId || courseState.currentId));

// Tab 在代码框里必须是缩进，不能跳走焦点
document.querySelector("#asm-code").addEventListener("keydown", (e) => {
  if (e.key !== "Tab") return;
  e.preventDefault();
  const el = e.target;
  const s = el.selectionStart, en = el.selectionEnd;
  el.value = el.value.slice(0, s) + "    " + el.value.slice(en);
  el.selectionStart = el.selectionEnd = s + 4;
  el.dispatchEvent(new Event("input"));
});

// 边打边存草稿：切题、刷新、误点返回都不至于丢
document.querySelector("#asm-code").addEventListener("input", () => {
  if (!asmState.currentKey) return;
  localStorage.setItem(asmDraftKey(asmState.currentKey), document.querySelector("#asm-code").value);
});

document.querySelector("#btn-asm-hint").onclick = () => {
  const t = asmState.tasks.find(x => x.key === asmState.currentKey);
  if (!t) return;
  const box = document.querySelector("#asm-hint-box");
  const open = box.classList.toggle("hidden") === false;
  if (open && !box.innerHTML) {
    box.innerHTML = `<div class="asm-label">提示（按需展开，别一次看完）</div>`
      + `<ol>${(t.hints || []).map(h => `<li>${esc(h)}</li>`).join("")}</ol>`;
  }
  if (open) box.scrollIntoView({ block: "nearest", behavior: "smooth" });
};

document.querySelector("#btn-asm-ref").onclick = () => {
  const box = document.querySelector("#asm-ref-box");
  const open = box.classList.toggle("hidden") === false;
  if (!open) return;
  if (!box.textContent.trim()) box.textContent = "提交一次之后才会拿到参考答案。";
  box.scrollIntoView({ block: "nearest", behavior: "smooth" });
};

document.querySelector("#btn-asm-submit").onclick = async () => {
  if (asmState.busy) return;
  const key = asmState.currentKey;
  const code = document.querySelector("#asm-code").value.trim();
  if (!code) return toast("先写点代码再提交");
  const btn = document.querySelector("#btn-asm-submit");
  const fb = document.querySelector("#asm-feedback");
  asmState.busy = true;
  btn.disabled = true;
  btn.textContent = "批改中…";
  fb.innerHTML = `<div class="asm-empty">AI 正在逐条核对…（一般 10–20 秒）</div>`;
  try {
    const r = await api(`/api/courses/${asmState.courseId}/asm/grade`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_key: key, code }),
    });
    renderAsmFeedback(r.result);
    const refBox = document.querySelector("#asm-ref-box");
    refBox.textContent = r.reference || "";
    refBox.classList.add("hidden");

    const prev = asmState.progress[key] || { best: 0, tries: 0 };
    asmState.progress[key] = {
      best: Math.max(prev.best || 0, r.result.score || 0),
      tries: (prev.tries || 0) + 1,
    };
    document.querySelector("#asm-score").textContent =
      `最好 ${asmState.progress[key].best}/10 · 提交过 ${asmState.progress[key].tries} 次`;
    renderAsmList();
    // 批改结果在编辑器下方，不滚一下等于没反馈
    fb.scrollIntoView({ block: "nearest", behavior: "smooth" });
  } catch (e) {
    fb.innerHTML = `<div class="asm-empty">${esc(e.message)}</div>`;
  } finally {
    asmState.busy = false;
    btn.disabled = false;
    btn.textContent = "提交批改";
  }
};
