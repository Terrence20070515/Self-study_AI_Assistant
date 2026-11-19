"""检查前端各个 .js 的顶层声明有没有重名。

这个项目的前端是「一堆普通 <script> 顺序加载」，没有模块作用域 ——
`function blankInputs()` 在两个文件里各写一次，后加载的会**静默覆盖**前一个，
而且只在使用到那一页时才炸，极难发现。

真实事故（2026-11-19）：views-sqltrain.js 也定义了 blankInputs，
覆盖了 views-asm.js 的同名函数。汇编训练点「提交检查」时，读到的是
隐藏的 SQL 视图里残留的输入框（第一个还留着上次草稿的 "select"），
于是明明写对的答案被判 0/3。

用法：python scripts/check_frontend_dups.py
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 顶层声明：行首没有缩进（缩进的是函数体内部的局部变量，不算）
DECL = re.compile(
    r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"      # function foo()
    r"|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)"          # const foo =
)


def main():
    seen = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "frontend", "*.js"))):
        name_file = os.path.basename(path)
        for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
            m = DECL.match(line)
            if not m:
                continue
            name = m.group(1) or m.group(2)
            seen.setdefault(name, []).append((name_file, lineno))

    dups = {k: v for k, v in seen.items() if len({f for f, _ in v}) > 1}
    if not dups:
        print(f"✓ 顶层声明无重名（检查 {len(seen)} 个名字）")
        return

    print(f"✗ 发现 {len(dups)} 个跨文件重名 —— 后加载的会覆盖前一个：")
    for name, places in sorted(dups.items()):
        detail = "、".join(f"{f}:{n}" for f, n in places)
        print(f"  {name:<24} {detail}")
    sys.exit(1)


if __name__ == "__main__":
    main()
