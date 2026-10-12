"""问答与出题（流式 SSE）。"""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .. import core
from ..deps import course_or_404

router = APIRouter()

@router.post("/api/courses/{cid}/chat")
async def api_chat(cid: str, body: dict):
    course_or_404(cid)
    question = (body.get("question") or "").strip()
    mode = body.get("mode", "ask")
    # 「允许外部资料」开关：开启后检索范围扩到全部课程，且允许模型用自有知识补充
    allow_external = bool(body.get("allow_external"))
    if mode == "ask" and not question:
        raise HTTPException(400, "问题不能为空")

    def gen():
        for event in core.stream_chat(cid, question, mode, allow_external=allow_external):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/api/courses/{cid}/quiz")
def api_quiz(cid: str, body: dict):
    course_or_404(cid)
    material_ids = [m for m in (body.get("material_ids") or []) if isinstance(m, str)]
    if not material_ids:
        raise HTTPException(400, "请至少选择一份资料作为出题范围")
    try:
        num = min(max(int(body.get("num", 5)), 1), 20)
    except (TypeError, ValueError):
        num = 5
    kind = body.get("kind", "mixed")
    try:
        return core.generate_quiz(material_ids, num=num, kind=kind)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:  # 未配置 API Key 等
        raise HTTPException(400, str(e))
