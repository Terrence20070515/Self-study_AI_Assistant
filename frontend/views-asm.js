/* 汇编训练（填空版）：给完整骨架，只填挖掉的那几行。

为什么不做「从零手敲」：填空题能一眼核对 —— 哪一行对、哪一行错、
正确答案是什么，都在原地看得见。手敲整段反而没法验证对错。

判分在后端做逐空比对（归一化大小写/空白/逗号），不走模型：
填空只有一行指令，确定性匹配比语义判断更靠谱，也快得多。
*/

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
    <span class="asm-list-pass">满分 ${passed}</span>`;
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
         <em>${esc(t.source)} · ${esc(t.level)}</em>
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
  document.querySelector("#asm-meta").textContent = `${t.level} · ${t.source}`;
  document.querySelector("#asm-brief").textContent = t.brief;
  document.querySelector("#asm-decls").textContent = t.decls;

  const hint = document.querySelector("#asm-hint-box");
  hint.classList.add("hidden");
  hint.innerHTML = "";
  document.querySelector("#asm-result").innerHTML = "";

  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(asmDraftKey(key)) || "null");
  } catch { saved = null; }
  renderAsmCode(t, saved);

  const p = asmState.progress[key];
  document.querySelector("#asm-score").textContent =
    p ? `最好 ${p.best}/10 · 提交过 ${p.tries} 次` : "还没做过";
  renderAsmList();
}

// ---------- 渲染：行号 + 静态代码 + 空位输入框 ----------
function renderAsmCode(task, saved) {
  const box = document.querySelector("#asm-code");
  box.innerHTML = "";
  let idx = 0;

  task.parts.forEach(part => {
    if (part.label) {
      const lab = document.createElement("div");
      lab.className = "asm-part";
      lab.textContent = part.label;
      box.appendChild(lab);
    }
    part.lines.forEach((line, i) => {
      const row = document.createElement("div");
      row.className = "asm-line";

      const num = document.createElement("span");
      num.className = "asm-ln";
      num.textContent = i + 1;
      row.appendChild(num);

      const src = document.createElement("span");
      src.className = "asm-src";

      if (line.includes("____")) {
        const [pre, post] = line.split("____");
        if (pre) src.appendChild(document.createTextNode(pre));
        const inp = document.createElement("input");
        inp.className = "asm-blank";
        inp.dataset.blank = String(idx);
        inp.value = (saved && saved[idx]) || "";
        inp.spellcheck = false;
        inp.autocomplete = "off";
        inp.placeholder = "____";
        inp.addEventListener("input", saveAsmDraft);
        inp.addEventListener("keydown", onBlankKey);
        src.appendChild(inp);
        idx++;
        if (post) src.appendChild(document.createTextNode(post));
      } else {
        src.textContent = line || " ";
      }

      row.appendChild(src);
      box.appendChild(row);
    });
  });
}

function blankInputs() {
  return [...document.querySelectorAll("#asm-code .asm-blank")];
}

function saveAsmDraft() {
  if (!asmState.currentKey) return;
  const answers = blankInputs().map(i => i.value);
  localStorage.setItem(asmDraftKey(asmState.currentKey), JSON.stringify(answers));
}

function onBlankKey(e) {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const inputs = blankInputs();
  const i = inputs.indexOf(e.target);
  if (i >= 0 && i < inputs.length - 1) inputs[i + 1].focus();
  else checkAsm();          // 最后一个空按 Enter 直接检查
}

// ---------- 检查 ----------
function renderAsmResult(res) {
  const box = document.querySelector("#asm-result");
  const full = res.correct === res.total;
  const band = full ? "ok" : (res.correct > 0 ? "half" : "bad");

  // 原地标注每个空：对绿、错红、指令对但操作数错则黄
  const inputs = blankInputs();
  (res.items || []).forEach(it => {
    const inp = inputs[it.index];
    if (!inp) return;
    inp.classList.remove("ok", "bad", "near");
    inp.classList.add(it.ok ? "ok" : (it.near ? "near" : "bad"));
    const old = inp.parentElement.querySelector(".asm-answer");
    if (old) old.remove();
    if (!it.ok) {
      const tip = document.createElement("span");
      tip.className = "asm-answer";
      tip.textContent = "← " + it.expected;
      inp.parentElement.appendChild(tip);
    }
  });

  const rows = (res.items || []).filter(it => !it.ok).map(it =>
    `<div class="asm-row">
       <span class="asm-row-tag">第 ${it.index + 1} 空</span>
       <div class="asm-row-body">
         <div class="asm-row-line">
           <code>${esc(it.got || "（空）")}</code>
           <span class="asm-row-arrow">→</span>
           <code class="asm-row-right">${esc(it.expected)}</code>
         </div>
         <div class="asm-row-why">${esc(it.why || it.hint || "")}</div>
       </div>
     </div>`).join("");

  box.innerHTML =
    `<div class="asm-score-row">
       <span class="asm-big ${band}">${res.correct}<i>/${res.total} 空</i></span>
       <span class="asm-verdict">${full
         ? "全对。这道题的关键机制：" + esc(res.note || "")
         : `还有 ${res.total - res.correct} 个空要改，看下面逐条解释`}</span>
     </div>`
    + (rows ? `<div class="asm-rows">${rows}</div>` : "")
    + (full && res.note ? `<div class="asm-note">${esc(res.note)}</div>` : "");

  // 聚焦第一个错的，省得自己找
  const firstBad = (res.items || []).find(it => !it.ok);
  if (firstBad) {
    const inp = inputs[firstBad.index];
    if (inp) {
      inp.focus();
      inp.select();
    }
  }
  box.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

async function checkAsm() {
  if (asmState.busy || !asmState.currentKey) return;
  const answers = blankInputs().map(i => i.value);
  if (!answers.some(a => a.trim())) return toast("先填几个空再检查");
  const btn = document.querySelector("#btn-asm-check");
  const box = document.querySelector("#asm-result");
  asmState.busy = true;
  btn.disabled = true;
  btn.textContent = "检查中…";
  box.innerHTML = `<div class="asm-empty">正在核对…</div>`;
  try {
    const r = await api(`/api/courses/${asmState.courseId}/asm/check`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_key: asmState.currentKey, answers }),
    });
    renderAsmResult(r.result);
    const prev = asmState.progress[asmState.currentKey] || { best: 0, tries: 0 };
    asmState.progress[asmState.currentKey] = {
      best: Math.max(prev.best || 0, r.result.score || 0),
      tries: (prev.tries || 0) + 1,
    };
    document.querySelector("#asm-score").textContent =
      `最好 ${asmState.progress[asmState.currentKey].best}/10 · 提交过 ${asmState.progress[asmState.currentKey].tries} 次`;
    renderAsmList();
  } catch (e) {
    box.innerHTML = `<div class="asm-empty">${esc(e.message)}</div>`;
  } finally {
    asmState.busy = false;
    btn.disabled = false;
    btn.textContent = "提交检查";
  }
}

// ---------- 事件 ----------
document.querySelector("#btn-asm").onclick = guard("打开汇编训练", () => openAsmPage(courseState.currentId));
document.querySelector("#btn-asm-back").onclick = guard("返回互动学习", () => openCourseChat(asmState.courseId || courseState.currentId));
document.querySelector("#btn-asm-check").onclick = guard("提交检查", checkAsm);

document.querySelector("#btn-asm-hint").onclick = () => {
  const t = asmState.tasks.find(x => x.key === asmState.currentKey);
  if (!t) return;
  const box = document.querySelector("#asm-hint-box");
  const open = box.classList.toggle("hidden") === false;
  if (open && !box.innerHTML) {
    box.innerHTML = `<div class="asm-label">提示（只给你该往哪个方向想，不直接给答案）</div>`
      + `<ol>${(t.blanks || []).map((b, i) =>
          `<li><b>第 ${i + 1} 空</b>：${esc(b.hint || "")}</li>`).join("")}</ol>`;
  }
  if (open) box.scrollIntoView({ block: "nearest", behavior: "smooth" });
};

document.querySelector("#btn-asm-clear").onclick = () => {
  blankInputs().forEach(i => {
    i.value = "";
    i.classList.remove("ok", "bad", "near");
    const tip = i.parentElement.querySelector(".asm-answer");
    if (tip) tip.remove();
  });
  document.querySelector("#asm-result").innerHTML = "";
  saveAsmDraft();
};
