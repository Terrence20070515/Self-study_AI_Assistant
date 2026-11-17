"""知识图路由：每门课一张可长期维护的概念图。

节点表示知识点，点一下跳到资料的某一页。连线是自由的、但必须带类型
（属于 / 依赖 / 对比）—— 无名线过一个月连自己都看不懂。
不存任何进度、正确率、页码统计。
"""
from fastapi import APIRouter, HTTPException

from .. import core, store
from ..deps import course_or_404

router = APIRouter()


@router.get("/api/courses/{cid}/map")
def api_map_get(cid: str):
    course_or_404(cid)
    data = store.kg_get(cid)
    data["has_nodes"] = bool(data["nodes"])
    return data


@router.post("/api/courses/{cid}/map/nodes")
def api_map_add_node(cid: str, body: dict):
    course_or_404(cid)
    return store.kg_add_node(
        cid,
        label=str(body.get("label") or "")[:80],
        material_id=str(body.get("material_id") or ""),
        page=int(body.get("page") or 0),
        parent_id=int(body.get("parent_id") or 0),
        x=float(body.get("x") or 0),
        y=float(body.get("y") or 0),
    )


@router.patch("/api/map/nodes/{nid}")
def api_map_update_node(nid: int, body: dict):
    fields = {k: v for k, v in body.items() if k in store.NODE_FIELDS}
    if not fields:
        raise HTTPException(400, "没有可更新的字段")
    try:
        ok = store.kg_update_node(nid, **fields)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok:
        raise HTTPException(404, "节点不存在")
    return {"ok": True}


@router.delete("/api/map/nodes/{nid}")
def api_map_delete_node(nid: int):
    res = store.kg_delete_node(nid)
    if not res["deleted"]:
        raise HTTPException(404, "节点不存在")
    return res


@router.post("/api/courses/{cid}/map/edges")
def api_map_add_edge(cid: str, body: dict):
    course_or_404(cid)
    try:
        return store.kg_add_edge(
            cid,
            int(body.get("from_id") or 0),
            int(body.get("to_id") or 0),
            str(body.get("kind") or "belongs"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/map/edges/{eid}")
def api_map_delete_edge(eid: int):
    if not store.kg_delete_edge(eid):
        raise HTTPException(404, "连线不存在")
    return {"ok": True}


@router.post("/api/courses/{cid}/map/draft")
def api_map_draft(cid: str, body: dict):
    """按勾选的资料生成草稿，追加到现有图里（不覆盖用户已经改过的部分）。"""
    course_or_404(cid)
    ids = [str(x) for x in (body.get("material_ids") or []) if x]
    if not ids:
        raise HTTPException(400, "请先选择资料")
    try:
        draft = core.generate_map_draft(cid, ids)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:                      # 模型/网络问题：给用户一句能懂的
        raise HTTPException(502, f"生成失败：{type(e).__name__}")
    # 追加时把草稿整块挪到已有内容下方：草稿坐标从 0 开始，直接落上去会和
    # 用户已经摆好的节点叠在一起
    existing = store.kg_get(cid)["nodes"]
    if existing:
        base = max(n["y"] for n in existing) + 150
        for n in draft["nodes"]:
            n["y"] = float(n["y"]) + base
    store.kg_add_many(cid, draft["nodes"])
    return {"ok": True, "added": len(draft["nodes"]), "map": store.kg_get(cid)}
