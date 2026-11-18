/* AI 出题页：与「批量导入」同级的独立入口。
   这里只管「进出页面 + 选课程 + 加载资料」，出题本身仍在 views-quiz.js。
   分开的原因：出题是独立作业（跨课程、想刷哪门刷哪门），
   而「互动学习」是跟着当前课程的问答，两者的上下文不该互相绑死。 */

// 可出题的课程：未分类只是中转区，不该出现在下拉里
function quizCourses() {
  return (courseState.list || []).filter(c => c.code !== "UNFILED");
}

function renderQuizCourseSelect() {
  const sel = $("#quiz-course-select");
  if (!sel) return;
  const list = quizCourses();
  if (!list.length) {
    sel.innerHTML = `<option value="">还没有课程</option>`;
    sel.disabled = true;
    quizState.courseId = null;
    return;
  }
  sel.disabled = false;
  sel.innerHTML = list.map(c =>
    `<option value="${c.id}">${esc(c.code)}${c.name ? " · " + esc(c.name) : ""}</option>`).join("");
  // 记住上次选的那门；不在了就回到第一门
  if (quizState.courseId && list.some(c => c.id === quizState.courseId)) {
    sel.value = quizState.courseId;
  } else {
    quizState.courseId = list[0].id;
    sel.value = list[0].id;
  }
}

async function loadQuizPage() {
  // 正常进出出题页：作废「回到这道题」的回程票（题卡会被重建，回不去了）
  quizReturn = null;
  showQuizReturn(false);
  renderQuizCourseSelect();
  const result = $("#quiz-result");
  const cid = quizCourseId();
  // 换课程等于换了一整套题：旧的作答进度不能留
  quizState.session = null;
  renderQuizBar();
  if (result) result.innerHTML = "";
  if (!cid) {
    quizState.materials = [];
    renderQuizScope();
    if (result) result.innerHTML =
      `<div class="quiz-empty">还没有可出题的课程：先用「批量导入」上传资料，或新建一门课。</div>`;
    return;
  }
  try {
    quizState.materials = await api(`/api/courses/${cid}/materials`);
  } catch (e) {
    quizState.materials = [];
    toast("资料加载失败：" + e.message);
  }
  // 换课程后，上一门课勾选的资料要清掉（否则会拿着 A 课的 id 去 B 课出题）
  const alive = new Set(quizState.materials.map(m => m.id));
  for (const id of [...quizState.selected]) if (!alive.has(id)) quizState.selected.delete(id);
  renderQuizScope();
  if (!quizCandidates().length && result) {
    const total = quizState.materials.length;
    result.innerHTML = `<div class="quiz-empty">` + (total
      ? `这门课的 ${total} 份资料还没解析成功，等解析完再出题。`
      : `这门课还没有资料，先去课程里上传。`) + `</div>`;
  }
  await loadCoverage();
  loadQuizPending();      // 未完成的练习（按批次归档），不 await，别挡住页面
}

async function openQuizPage(courseId) {
  if (courseId) quizState.courseId = courseId;
  showView("quiz");
  // 页头「← 返回」统一回主页（和资料总库 / 错题本 / 均分计算一致）
  await loadQuizPage();
}

// 从出题页跳回某门课的问答（答错 → 让 AI 讲讲，落点必须是那门课的对话）
async function openCourseChat(courseId) {
  const cid = courseId || courseState.currentId;
  if (!cid) { showView("home"); return; }
  if (cid !== courseState.currentId) await openCourse(cid);   // 内部会 showView + 加载资料/对话
  else showView("course");
  switchTab("study");
}

// ---------- 入口 ----------
// 侧栏的「AI 出题」已删，主页是唯一入口（#dash-quiz）
// 主页快捷方式
$("#dash-quiz").onclick = guard("打开 AI 出题", () => openQuizPage());
// 课程页右上角：带上当前课程直接进（省得再去下拉里找一遍）
$("#btn-course-quiz").onclick = guard("去出题", () => openQuizPage(courseState.currentId));
// 底部的「返回最上层」是全局的，绑在 core.js 的 showView 旁边

$("#quiz-course-select").onchange = guard("切换出题课程", async (e) => {
  quizState.courseId = e.target.value;
  quizState.scopeTag = "";                       // 换课程后标签筛选归零
  quizState.selected.clear();
  document.querySelectorAll("#quiz-tag-filter .chip")
    .forEach(c => c.classList.toggle("active", c.dataset.tag === ""));
  await loadQuizPage();
});
