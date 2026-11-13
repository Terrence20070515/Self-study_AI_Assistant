"""把已有的 Word 资料批量转成 PDF，转完重新解析（页码变成真实页）。

前提：装了 LibreOffice。装好后在 study-tool 目录下执行：

    /Users/terrence/.workbuddy/binaries/python/envs/default/bin/python tools/convert_docx_batch.py

转换后这些 Word 资料就和 PDF 完全同构了：沉浸模式、圈画、逐页注释、页图、
文字层选择全部可用；导出/下载仍给原始 .docx，不受影响。

注意：页码会从一个「文本块序号」变成真实页码，之前基于旧 unit_key 出的题
对不上新页码（覆盖率台账也会把它们当新知识点），需要的话重新出题即可。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import core, store          # noqa: E402
from backend.config import material_file_path   # noqa: E402


def main() -> int:
    exe = core.soffice_path()
    if not exe:
        print("没找到 LibreOffice，先装：")
        print("  1) 下载 https://www.libreoffice.org/download/download-libreoffice/")
        print("     （选 macOS · Apple Silicon / Intel）")
        print("  2) 打开 dmg，把 LibreOffice 拖进「应用程序」")
        print("  3) 回来重跑这个脚本")
        return 1
    print(f"使用 {exe}\n")

    docs = [m for m in store.materials_with_course()
            if (m.get("ext") or "").lower() == "docx"]
    if not docs:
        print("没有 Word 资料")
        return 0

    print(f"共 {len(docs)} 份 Word 资料\n")
    ok, failed = 0, []
    for m in docs:
        src = material_file_path(m["id"], "docx")
        out = core.convert_docx_to_pdf(src)
        if not out:
            failed.append(m["orig_name"])
            print(f"  ✗ {m['orig_name'][:56]}")
            continue
        size_kb = os.path.getsize(out) // 1024
        print(f"  ✓ {m['orig_name'][:56]}  → {size_kb} KB", flush=True)
        # 用 PDF 重新解析：chunk 会按真实页重切，add_chunks 是幂等的不会重复
        core.process_material(m["id"])
        ok += 1

    print(f"\n完成 {ok}/{len(docs)}")
    if failed:
        print("以下文件转换失败（可能加密或格式特殊）：")
        for n in failed:
            print(f"  - {n}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
