"""SQL 训练（SOE101）：选择题 + SQL 填空，全部本地判分，不调模型。

题型照着课程那份 CPT103 SQL Revision 来：
  · choice  三值逻辑求值、概念多选 —— 选中集合与答案集合完全一致才算对
  · blank   给 SQL 骨架挖空 —— 按 accept 归一化比对（大小写、空白、逗号空格、结尾分号都忽略）

为什么不上模型判分：选一个 SQL 关键字这种事，确定性比对比语义判断更准也更快；
写完整查询才需要语义判断，而那类题这里不做（没有执行环境就没法真正验证）。
"""
import re

from fastapi import APIRouter, HTTPException

from .. import store
from ..deps import course_or_404
from ..sql_tasks import SQL_TASK_MAP, SQL_TASKS, answer_key, public_task

router = APIRouter()

# 题库是 SOE101（Introduction to Database）口径，其它课程不显示入口
SQL_COURSE_CODES = {"SOE101"}


def _supported(course: dict) -> bool:
    return (course.get("code") or "").upper() in SQL_COURSE_CODES


def _norm(s: str) -> str:
    """归一化：大小写、空白、逗号两侧空隙、结尾分号都不算错。"""
    s = (s or "").strip().lower()
    s = re.sub(r"\s*,\s*", ", ", s)      # "char(4),not null" -> "char(4), not null"
    s = re.sub(r"\s+", " ", s)
    return s.strip().rstrip(";")


@router.get("/api/courses/{cid}/sqltrain/tasks")
def api_sql_tasks(cid: str):
    course = course_or_404(cid)
    ok = _supported(course)
    return {
        "supported": ok,
        "tasks": [public_task(t) for t in SQL_TASKS] if ok else [],
        "progress": store.sqltrain_progress(cid) if ok else {},
    }


@router.post("/api/courses/{cid}/sqltrain/check")
def api_sql_check(cid: str, body: dict):
    """判分。body: {task_key, picks: ["A","C"]} 或 {task_key, answers: ["...", ...]}"""
    course = course_or_404(cid)
    if not _supported(course):
        raise HTTPException(400, "这门课还没有 SQL 训练题库")

    key = str(body.get("task_key") or "").strip()
    task = SQL_TASK_MAP.get(key)
    if not task:
        raise HTTPException(404, "没有这道题")

    if task["kind"] == "choice":
        picks = [str(x).strip().upper() for x in (body.get("picks") or []) if str(x).strip()]
        picks = sorted({p for p in picks if p in "ABCDEF"})
        want = sorted(task["answer"])
        ok = picks == want
        detail = {
            "kind": "choice",
            "score": 1 if ok else 0,
            "total": 1,
            "picked": picks,
            "answer": want,
            # 逐项标注：对答案里的项，选中=绿、未选=漏；不在答案里的项，选中=红
            "options": [
                {"letter": chr(65 + i),
                 "correct": chr(65 + i) in want,
                 "picked": chr(65 + i) in picks}
                for i in range(len(task["options"]))
            ],
            "why": task.get("note", ""),
        }
        store.add_sqltrain_attempt(cid, key, detail["score"], 1, detail)
        return detail

    raw = body.get("answers")
    if not isinstance(raw, list):
        raise HTTPException(400, "answers 必须是数组")
    if len(raw) != len(task["blanks"]):
        raise HTTPException(400, f"这道题有 {len(task['blanks'])} 个空，收到 {len(raw)} 个答案")

    blanks = []
    score = 0
    for i, b in enumerate(task["blanks"]):
        mine = _norm(str(raw[i] if i < len(raw) else ""))
        accept = [_norm(a) for a in b.get("accept", [])]
        ok = mine in accept
        if ok:
            score += 1
        blanks.append({
            "ok": ok,
            "answer": b["accept"][0] if b.get("accept") else "",
            "yours": str(raw[i] if i < len(raw) else "").strip(),
            "why": b.get("why", ""),
        })
    detail = {
        "kind": "blank",
        "score": score,
        "total": len(task["blanks"]),
        "blanks": blanks,
        "note": task.get("note", ""),
    }
    store.add_sqltrain_attempt(cid, key, score, len(task["blanks"]), detail)
    return detail


@router.get("/api/courses/{cid}/sqltrain/tasks/{task_key}/answer")
def api_sql_answer(cid: str, task_key: str):
    """「看答案」用：只在用户主动点了之后返回，不在列表里一次全给。"""
    course = course_or_404(cid)
    if not _supported(course):
        raise HTTPException(400, "这门课还没有 SQL 训练题库")
    task = SQL_TASK_MAP.get(task_key)
    if not task:
        raise HTTPException(404, "没有这道题")
    return answer_key(task)
