/* 错题本：跨课程汇总「最近一次作答仍错」的题，按课程 → 资料分组。
   数据来自 /api/wrongbook；重做走现有的 /api/quiz/questions/{id}/attempt，
   答对后这道题会因为「最近一次是正确」而自动从清单里消失。 */

const wbState = { data: null, weak: null, busy: false };

const wbEsc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

const letter = (i) => String.fromCharCode(65 + i);

function wbAnswerLetter(v) {
  // 答案可能是 "B"、"B. xxx" 或完整选项文本，统一取首字母
  const t = String(v || "").trim();
  const m = t.match(/^([A-Fa-f])\b/) || t.match(/^([A-Fa-f])$/);
  return m ? m[1].toUpperCase() : t;
}

/* ---------------- 渲染 ---------------- */

function wbOptions(q) {
  const ans = wbAnswerLetter(q.answer);
  const mine = wbAnswerLetter(q.user_answer);
  return `<div class="wb-opts">${(q.options || []).map((o, k) => {
    const L = letter(k);
    const cls = L === ans ? " right" : (L === mine ? " wrong" : "");
    const mark = L === ans ? "正确" : (L === mine ? "你的选择" : "");
    return `<div class="wb-opt${cls}"><i>${L}</i><span>${wbEsc(o)}</span>`
      + (mark ? `<em>${mark}</em>` : "") + `</div>`;
  }).join("")}</div>`;
}

function wbQuestion(q, mat) {
  const hasOpts = (q.options || []).length > 0;
  return `
    <div class="wb-q" data-qid="${q.id}">
      <div class="wb-q-text">${wbEsc(q.question)}</div>
      ${hasOpts ? wbOptions(q) : `<div class="wb-short">简答题 · 你的自评：
        <b class="${q.user_answer === "self:correct" ? "ok" : "bad"}">
        ${q.user_answer === "self:correct" ? "对" : "错"}</b></div>`}
      <div class="wb-meta">
        ${hasOpts ? `<span>你选 <b class="bad">${wbEsc(wbAnswerLetter(q.user_answer) || "—")}</b></span>
                     <span>正确 <b class="ok">${wbEsc(wbAnswerLetter(q.answer) || "—")}</b></span>` : ""}
        ${q.attempts > 1 ? `<span class="muted">答过 ${q.attempts} 次</span>` : ""}
        ${q.level ? `<span class="muted">${wbEsc(q.level)}</span>` : ""}
      </div>
      ${q.explanation ? `<details class="wb-exp"><summary>看解释</summary>
        <p>${wbEsc(q.explanation)}</p></details>` : ""}
      <div class="wb-actions">
        ${hasOpts ? `<button class="btn btn-outline btn-sm wb-redo">重做</button>` : ""}
        <button class="btn btn-ghost btn-sm wb-open"
                data-mid="${q.material_id}" data-name="${wbEsc(mat.orig_name)}"
                data-ext="${wbEsc(mat.ext || "pdf")}" data-page="${q.page || 1}">
          去原文${q.page ? " p." + q.page : ""}</button>
      </div>
    </div>`;
}

function wbMaterial(g, m) {
  return `
    <div class="wb-mat" data-mid="${wbEsc(m.material_id || "")}">
      <div class="wb-mat-head">
        <b>${wbEsc(m.orig_name || "未关联资料")}</b>
        <span>${m.questions.length} 道${m.page ? " · 约第 " + m.page + " 页" : ""}</span>
      </div>
      ${m.questions.map((q) => wbQuestion(q, m)).join("")}
    </div>`;
}

/* 薄弱点排行：错题本只告诉你「错了几道」，这里补上分母 ——
   错 7 道可能是从 8 道里错的（基本没掌握），也可能是从 40 道里错的（其实还行）。
   点一行滚到下面那份资料的题卡。 */
function wbWeakSection() {
  const w = wbState.weak;
  if (!w || !(w.items || []).length) return "";
  const level = (acc) => (acc < 60 ? "bad" : acc < 75 ? "warn" : "ok");
  return `
    <section class="wb-weak">
      <div class="wb-weak-head">
        <b>最该补的 ${w.items.length} 处</b>
        <span class="muted">按正确率排，点一行跳到下面的题</span>
        ${w.low_sample ? `<span class="wb-weak-note">另有 ${w.low_sample} 份答过不足 ${w.min_sample} 道，样本太少不参与排名</span>` : ""}
      </div>
      <div class="wb-weak-list">
        ${w.items.map((it) => `
          <button class="wb-weak-row" data-mid="${wbEsc(it.material_id)}">
            <span class="wb-weak-acc ${level(it.accuracy)}">${it.accuracy}%</span>
            <span class="wb-weak-name">${wbEsc(it.orig_name || "")}</span>
            <span class="wb-weak-num">${it.wrong}/${it.answered} 道错</span>
          </button>`).join("")}
      </div>
    </section>`;
}

function renderWrongBook() {
  const body = document.querySelector("#wb-body");
  const d = wbState.data;
  const groups = (d && d.groups) || [];
  document.querySelector("#wb-total").textContent =
    d && d.total ? `待解决 ${d.total} 道` : "";

  if (!groups.length) {
    body.innerHTML = `<div class="wb-empty">没有待解决的错题。<br>
      去「AI 出题」做一轮，答错的题会自动收进来。</div>`;
    return;
  }
  body.innerHTML = wbWeakSection() + groups.map((g) => `
    <section class="wb-course">
      <div class="wb-course-head">
        <b>${wbEsc(g.course_code)}</b>
        <span class="muted">${wbEsc(g.course_name || "")}</span>
        <span class="wb-count">${g.count} 道</span>
      </div>
      ${g.materials.map((m) => wbMaterial(g, m)).join("")}
    </section>`).join("");
  bindWrongBook();
}

async function loadWrongBook() {
  const body = document.querySelector("#wb-body");
  body.innerHTML = `<div class="wb-empty">读取中…</div>`;
  try {
    // 两个请求并发：排行和题卡本来就是同一份数据的两种切法
    const [book, weak] = await Promise.all([
      api("/api/wrongbook"),
      api("/api/weak-points?limit=8").catch(() => null),   // 排行挂了不该拖垮错题本
    ]);
    wbState.data = book;
    wbState.weak = weak;
  } catch (e) {
    body.innerHTML = `<div class="wb-empty">读取失败：${wbEsc(e.message)}</div>`;
    return;
  }
  renderWrongBook();
}

/* ---------------- 交互 ---------------- */

function bindWrongBook() {
  document.querySelectorAll(".wb-open").forEach((b) => {
    b.onclick = () => {
      openImmersive({ id: b.dataset.mid, orig_name: b.dataset.name,
                      ext: b.dataset.ext }, parseInt(b.dataset.page, 10) || 1);
    };
  });

  document.querySelectorAll(".wb-redo").forEach((btn) => {
    btn.onclick = () => startRedo(btn.closest(".wb-q"));
  });

  // 排行行 → 滚到下面那份资料的题卡，并短暂高亮
  document.querySelectorAll(".wb-weak-row").forEach((row) => {
    row.onclick = () => {
      const card = document.querySelector(`.wb-mat[data-mid="${row.dataset.mid}"]`);
      if (!card) return;
      card.scrollIntoView({ block: "center", behavior: "smooth" });
      card.classList.remove("wb-flash");
      void card.offsetWidth;          // 强制重排，否则重复点击不会再触发动画
      card.classList.add("wb-flash");
    };
  });
}

function startRedo(card) {
  const qid = parseInt(card.dataset.qid, 10);
  const q = findQuestion(qid);
  if (!q) return;

  const opts = card.querySelector(".wb-opts");
  if (!opts) return;
  // 重做期间藏起「正确 X」和解释，否则等于把答案摆在眼前
  card.querySelector(".wb-meta")?.classList.add("hidden");
  card.querySelector(".wb-exp")?.classList.add("hidden");

  opts.dataset.mode = "redo";
  opts.innerHTML = q.options.map((o, k) => `
    <button class="wb-opt wb-pick" data-letter="${letter(k)}">
      <i>${letter(k)}</i><span>${wbEsc(o)}</span>
    </button>`).join("");

  const tip = document.createElement("div");
  tip.className = "wb-tip";
  tip.textContent = "选一个，答对就移出错题本";
  opts.after(tip);

  opts.querySelectorAll(".wb-pick").forEach((b) => {
    b.onclick = () => submitRedo(card, qid, b.dataset.letter);
  });
}

async function submitRedo(card, qid, pick) {
  if (wbState.busy) return;
  wbState.busy = true;
  const tip = card.querySelector(".wb-tip");
  const opts = card.querySelector(".wb-opts");
  opts.querySelectorAll(".wb-pick").forEach((b) => (b.disabled = true));

  let r;
  try {
    r = await api(`/api/quiz/questions/${qid}/attempt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer: pick }),
    });
  } catch (e) {
    if (tip) tip.textContent = "提交失败：" + e.message;
    wbState.busy = false;
    return;
  }
  wbState.busy = false;

  // 就地标注：选中的那个 + 正确项
  const ans = wbAnswerLetter(r.answer);
  card.querySelector(".wb-meta")?.classList.remove("hidden");
  card.querySelector(".wb-exp")?.classList.remove("hidden");
  opts.querySelectorAll(".wb-pick").forEach((b) => {
    const L = b.dataset.letter;
    if (L === ans) b.classList.add("right");
    else if (L === pick) b.classList.add("wrong");
    b.classList.remove("wb-pick");
  });

  if (r.correct) {
    card.classList.add("resolved");
    if (tip) tip.innerHTML = `<b class="ok">答对了</b>，这道题已移出错题本`;
    setTimeout(loadWrongBook, 1400);
  } else {
    if (tip) tip.innerHTML = `<b class="bad">还是不对</b>。正确答案 ${ans}，`
      + `看看上面的解释，再点「去原文」回到出处`;
    setTimeout(() => loadWrongBook(), 2600);
  }
}

function findQuestion(qid) {
  for (const g of (wbState.data && wbState.data.groups) || []) {
    for (const m of g.materials) {
      for (const q of m.questions) if (q.id === qid) return q;
    }
  }
  return null;
}

/* ---------------- 入口 ---------------- */

document.querySelector("#dash-wrong").onclick = () => {
  showView("wrong");
  loadWrongBook();
};
document.querySelector("#btn-wrong-back").onclick = () => showHome();
