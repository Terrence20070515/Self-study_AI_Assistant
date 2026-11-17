"""速查表导出 PDF。

不用浏览器、不用外部工具：本机已有 PyMuPDF（解析 PDF 用的那个），
直接排版最稳 —— 沙箱里能不能起 Chrome，不该成为「导出按钮」能不能用的前提。

字体：优先用系统中文字体（Hiragino Sans GB / Songti）。PyMuPDF 内置的
`china-s` 也能写中文，但它把 Latin 也按全角渲染 —— 实测出来是
「S O E 1 0 1」这种字间距，非常难看。所以找到系统字体就用系统的，
找不到才退回 china-s。

排版：A4 单栏、9pt 正文，四段各一个浅色标题条，每条末尾印「资料名 p.N」。
"""
import datetime
import os
import re

import fitz

PAGE_W, PAGE_H = 595.0, 842.0          # A4
MARGIN = 44.0
CONTENT_W = PAGE_W - MARGIN * 2

FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)
_FALLBACK_NAME = "china-s"             # PyMuPDF 内置（Latin 会变全角，仅作兜底）

SECTION_LABEL = {
    "terms": "术语表",
    "formulas": "公式与规则",
    "code": "代码模板",
    "pitfalls": "易错点",
}
SECTION_ORDER = ("terms", "formulas", "code", "pitfalls")

_font_cache = {"font": None, "file": None, "loaded": False}


def _get_font():
    if _font_cache["loaded"]:
        return _font_cache["font"], _font_cache["file"]
    _font_cache["loaded"] = True
    for path in FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            _font_cache["font"] = fitz.Font(fontfile=path)
            _font_cache["file"] = path
            break
        except Exception:
            continue
    return _font_cache["font"], _font_cache["file"]


def _text_w(s: str, size: float) -> float:
    font, _ = _get_font()
    if font is not None:
        return font.text_length(s, size)
    # 兜底：内置字体全是等宽概念，按字号估
    return sum(size if ord(c) > 0x2E7F else size * 0.55 for c in s)


def _wrap(text: str, size: float, width: float) -> list:
    """按实际字宽贪心折行（保留原有换行）。"""
    font, _ = _get_font()
    out = []
    for raw in str(text or "").split("\n"):
        if not raw:
            out.append("")
            continue
        line, w = "", 0.0
        for ch in raw:
            cw = font.text_length(ch, size) if font is not None else _text_w(ch, size)
            if w + cw > width and line:
                out.append(line)
                line, w = ch, cw
            else:
                line += ch
                w += cw
        out.append(line)
    return out


class _Cursor:
    """逐行落笔的游标，空间不够就换页。"""

    def __init__(self, doc):
        self.doc = doc
        self.font, self.font_file = _get_font()
        self.page = None
        self.y = 0.0
        self.new_page()

    def new_page(self):
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        # 每一页都要登记一次字体，返回该页内可用的 fontname
        if self.font_file:
            # 用自己起的名字，不要用返回值：新版 PyMuPDF 的 insert_font
            # 返回的是字体 xref（int），拿去 insert_text 会直接 AttributeError
            self.page.insert_font(fontname="F1", fontfile=self.font_file)
            self.fname = "F1"
        else:
            self.fname = _FALLBACK_NAME
        self.y = MARGIN

    def need(self, h: float):
        if self.y + h > PAGE_H - MARGIN:
            self.new_page()

    def text(self, s: str, size: float = 9.0, indent: float = 0.0,
             color=(0, 0, 0), gap_after: float = 1.5):
        lines = _wrap(s, size, CONTENT_W - indent)
        line_h = size * 1.5
        for ln in lines:
            self.need(line_h)
            if ln:
                self.page.insert_text((MARGIN + indent, self.y + size), ln,
                                      fontname=self.fname, fontsize=size, color=color)
            self.y += line_h
        self.y += gap_after

    def bar(self, label: str):
        self.need(28)
        h = 20
        self.page.draw_rect(fitz.Rect(MARGIN, self.y, MARGIN + CONTENT_W, self.y + h),
                            color=None, fill=(0.93, 0.94, 0.96), width=0)
        self.page.insert_text((MARGIN + 9, self.y + 13.6), label,
                              fontname=self.fname, fontsize=10.5, color=(0.12, 0.13, 0.15))
        self.y += h + 8


def build_cheat_pdf(course_code: str, course_name: str, items: list) -> bytes:
    doc = fitz.open()
    cur = _Cursor(doc)

    cur.page.insert_text((MARGIN, cur.y + 17), f"{course_code} 速查表",
                         fontname=cur.fname, fontsize=17, color=(0.08, 0.09, 0.11))
    cur.y += 26
    if course_name:
        cur.page.insert_text((MARGIN, cur.y + 10), course_name,
                             fontname=cur.fname, fontsize=10, color=(0.35, 0.37, 0.4))
        cur.y += 16
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.page.insert_text((MARGIN, cur.y + 10), f"导出于 {stamp}",
                         fontname=cur.fname, fontsize=8, color=(0.55, 0.57, 0.6))
    cur.y += 22

    by_sec = {}
    for it in items:
        by_sec.setdefault(it.get("section") or "terms", []).append(it)

    wrote_any = False
    for sec in SECTION_ORDER:
        rows = by_sec.get(sec) or []
        if not rows:
            continue
        wrote_any = True
        cur.bar(SECTION_LABEL[sec])
        for i, it in enumerate(rows, 1):
            title = (it.get("title") or "").strip()
            body = (it.get("body") or "").strip()
            ref = ""
            if it.get("page"):
                name = (it.get("orig_name") or "").strip()
                # 资料名太长会挤掉正文，只留末尾识别度最高的部分
                if len(name) > 26:
                    name = "…" + name[-25:]      # 末尾识别度最高（含课程/章节号）
                ref = f"{name} p.{it['page']}" if name else f"p.{it['page']}"

            if title:
                cur.text(f"{i}. {title}", size=10, color=(0.10, 0.11, 0.13), gap_after=0.8)
            if body:
                cur.text(body, size=8.8 if sec == "code" else 9, indent=8,
                         color=(0.18, 0.19, 0.22), gap_after=0.8)
            if ref:
                cur.text(ref, size=7.4, indent=8, color=(0.55, 0.57, 0.6), gap_after=5.0)
            else:
                cur.y += 4

    if not wrote_any:
        cur.text("（还没有内容）", size=10, color=(0.55, 0.57, 0.6))

    total = len(doc)
    for i, page in enumerate(doc, 1):
        # 页码用内置字体就够（纯数字），不必再登记一次
        page.insert_text((PAGE_W / 2 - 14, PAGE_H - 22), f"{i} / {total}",
                         fontname="helv", fontsize=8, color=(0.6, 0.62, 0.65))

    # 系统字体是几十 MB 的 ttc，整份嵌进去会让一页速查表变成 13 MB。
    # subset_fonts 只保留实际用到的字形，体积立刻回到几十 KB。
    try:
        doc.subset_fonts()
    except Exception:
        pass
    data = doc.tobytes()
    doc.close()
    return data


def safe_filename(s: str) -> str:
    """文件名只留 ASCII，避免下载头里出现非 ASCII 又要编码。"""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", (s or "cheat")).strip("_") or "cheat"
