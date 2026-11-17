"""速查表路由：应用内可编辑的四段速查页 + 一键导出 PDF。

同一份内容两条出口：页面上能随时改（发现老忘的点就加一行），
PDF 是打印/塞手机用的终点。所以 PDF 每次都按当前库里的内容重新生成，
不做缓存 —— 改完导出必须是最新的。
"""
from fastapi import APIRouter, HTTPException, Response

from .. import core, pdfexport, store
from ..deps import course_or_404

router = APIRouter()


@router.get("/api/courses/{cid}/cheat")
def api_cheat_get(cid: str):
    course_or_404(cid)
    data = store.cheat_list(cid)
    data["sections"] = list(store.CHEAT_SECTIONS)
    return data


@router.post("/api/courses/{cid}/cheat/generate")
def api_cheat_generate(cid: str, body: dict):
    """按勾选的资料重生成整份速查表（会覆盖现有内容，前端先确认过）。"""
    course_or_404(cid)
    ids = [str(x) for x in (body.get("material_ids") or []) if x]
    if not ids:
        raise HTTPException(400, "请先选择资料")
    try:
        items = core.generate_cheat(cid, ids)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"生成失败：{type(e).__name__}")
    n = store.cheat_replace(cid, items)
    return {"ok": True, "added": n, "data": store.cheat_list(cid)}


@router.post("/api/courses/{cid}/cheat/items")
def api_cheat_add(cid: str, body: dict):
    course_or_404(cid)
    return store.cheat_add_item(
        cid,
        section=str(body.get("section") or "terms"),
        title=str(body.get("title") or ""),
        body=str(body.get("body") or ""),
        material_id=str(body.get("material_id") or ""),
        page=int(body.get("page") or 0),
    )


@router.patch("/api/cheat/items/{iid}")
def api_cheat_update(iid: int, body: dict):
    fields = {k: v for k, v in body.items() if k in store.CHEAT_FIELDS}
    if not fields:
        raise HTTPException(400, "没有可更新的字段")
    try:
        ok = store.cheat_update_item(iid, **fields)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok:
        raise HTTPException(404, "条目不存在")
    return {"ok": True}


@router.delete("/api/cheat/items/{iid}")
def api_cheat_delete(iid: int):
    if not store.cheat_delete_item(iid):
        raise HTTPException(404, "条目不存在")
    return {"ok": True}


@router.get("/api/courses/{cid}/cheat.pdf")
def api_cheat_pdf(cid: str):
    co = course_or_404(cid)
    data = store.cheat_list(cid)
    if not data["items"]:
        raise HTTPException(400, "速查表还是空的")
    pdf = pdfexport.build_cheat_pdf(co.get("code") or "", co.get("name") or "", data["items"])
    name = f"{pdfexport.safe_filename(co.get('code') or 'cheat')}-cheatsheet.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
