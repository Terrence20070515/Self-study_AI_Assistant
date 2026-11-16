"""汇编训练（填空版）：给骨架、挖空、学生填指令。

判分是**逐空精确比对**，不走模型：
    · 填空只有一行指令，确定性匹配比语义判断更靠谱，也更快
    · 归一化忽略大小写、空白数量、逗号两侧空格
    · 每个空自带 accept（可接受写法）、hint（提示）、why（填错时的解释）
这样「对没对」一眼可见，不用等模型、也不用猜它为什么给这个分。
"""
import json
import re

from fastapi import APIRouter, HTTPException

from .. import store
from ..asm_tasks import ASM_TASK_MAP, ASM_TASKS, answer_key, public_task
from ..deps import course_or_404

router = APIRouter()

# 目前题库只针对这门课（Computer Systems 的 x86 汇编模块）
ASM_COURSE_CODES = {"CSI101", "CPT101"}


def _ensure_supported(course: dict):
    if (course.get("code") or "").upper() not in ASM_COURSE_CODES:
        raise HTTPException(400, "这门课还没有汇编训练题库")


def _norm(s: str) -> str:
    """归一化：大小写、空白、逗号两侧空格都不算错。"""
    s = (s or "").strip().lower()
    s = re.sub(r"\s*,\s*", ", ", s)      # "cmp eax,ebx" -> "cmp eax, ebx"
    s = re.sub(r"\s+", " ", s)
    return s.strip()


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


@router.post("/api/courses/{cid}/asm/check")
def api_asm_check(cid: str, body: dict):
    """逐空判分。body: {task_key, answers: ["...", ...]}"""
    course = course_or_404(cid)
    _ensure_supported(course)
    key = str(body.get("task_key") or "").strip()
    task = ASM_TASK_MAP.get(key)
    if not task:
        raise HTTPException(404, "没有这道题")

    raw = body.get("answers")
    if not isinstance(raw, list):
        raise HTTPException(400, "answers 必须是数组")
    answers = [str(a or "") for a in raw][: len(task["blanks"])]
    answers += [""] * (len(task["blanks"]) - len(answers))

    items = []
    correct = 0
    for i, blank in enumerate(task["blanks"]):
        got = answers[i]
        accepts = [_norm(a) for a in blank.get("accept", [])]
        ok = _norm(got) in accepts and _norm(got) != ""
        if ok:
            correct += 1
        # 指令写对了但操作数不对 —— 单独提示，比笼统判错有用
        near = False
        if not ok and got.strip():
            head = _norm(got).split(" ")[0]
            near = any(a.split(" ")[0] == head for a in accepts)
        items.append({
            "index": i,
            "ok": ok,
            "got": got,
            "near": near,
            "expected": blank.get("accept", [""])[0],
            "why": blank.get("why", ""),
            "hint": blank.get("hint", ""),
        })

    total = len(task["blanks"])
    score = round(correct * 10 / total) if total else 0
    result = {
        "score": score,
        "correct": correct,
        "total": total,
        "items": items,
        "note": task.get("note", ""),
        "answers": answer_key(task),
    }
    aid = store.save_asm_attempt(cid, key, json.dumps(answers, ensure_ascii=False),
                                 score, result)
    return {"attempt_id": aid, "result": result}


@router.get("/api/courses/{cid}/asm/tasks/{key}/attempt")
def api_asm_last_attempt(cid: str, key: str):
    course = course_or_404(cid)
    _ensure_supported(course)
    if key not in ASM_TASK_MAP:
        raise HTTPException(404, "没有这道题")
    row = store.latest_asm_attempt(cid, key)
    if not row:
        return {"attempt": None}
    try:
        answers = json.loads(row["code"] or "[]")
    except Exception:
        answers = []
    return {"attempt": {
        "answers": answers,
        "score": row["score"],
        "feedback": row["feedback"],
        "created_at": row["created_at"],
    }}
