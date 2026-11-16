"""汇编训练：手打 x86 内联汇编 → AI 逐条批改。

题目内置在 asm_tasks.py，按课程代码限定（目前只挂在 CSI101 上）。
判分走 core.grade_asm()，语义等价即可，不逐字比对参考实现。
"""
from fastapi import APIRouter, HTTPException

from .. import core, store
from ..asm_tasks import ASM_TASKS, ASM_TASK_MAP, public_task
from ..deps import course_or_404

router = APIRouter()

# 目前题库只针对这门课（Computer Systems 的 x86 汇编模块）
ASM_COURSE_CODES = {"CSI101", "CPT101"}


def _ensure_supported(course: dict):
    if (course.get("code") or "").upper() not in ASM_COURSE_CODES:
        raise HTTPException(400, "这门课还没有汇编训练题库")


@router.get("/api/courses/{cid}/asm/tasks")
def api_asm_tasks(cid: str):
    course = course_or_404(cid)
    supported = (course.get("code") or "").upper() in ASM_COURSE_CODES
    tasks = [public_task(t) for t in ASM_TASKS] if supported else []
    return {
        "supported": supported,
        "tasks": tasks,
        "progress": store.asm_progress(cid) if supported else {},
    }


@router.post("/api/courses/{cid}/asm/grade")
def api_asm_grade(cid: str, body: dict):
    course = course_or_404(cid)
    _ensure_supported(course)
    key = str(body.get("task_key") or "").strip()
    task = ASM_TASK_MAP.get(key)
    if not task:
        raise HTTPException(404, "没有这道题")
    code = str(body.get("code") or "")
    if len(code) > 20000:
        raise HTTPException(400, "代码太长了")
    try:
        result = core.grade_asm(task, code)
    except Exception as e:
        raise HTTPException(502, f"批改失败：{type(e).__name__}: {e}")
    aid = store.save_asm_attempt(cid, key, code, result["score"], result)
    return {"attempt_id": aid, "result": result, "reference": task["reference"]}


@router.get("/api/courses/{cid}/asm/tasks/{key}/attempt")
def api_asm_last_attempt(cid: str, key: str):
    course = course_or_404(cid)
    _ensure_supported(course)
    if key not in ASM_TASK_MAP:
        raise HTTPException(404, "没有这道题")
    row = store.latest_asm_attempt(cid, key)
    if not row:
        return {"attempt": None}
    return {"attempt": {
        "code": row["code"],
        "score": row["score"],
        "feedback": row["feedback"],
        "created_at": row["created_at"],
        "reference": ASM_TASK_MAP[key]["reference"],
    }}
