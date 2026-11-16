"""汇编题库回归：把每道题的参考实现（accept[0]）跑一遍迷你模拟器，验证真的算对。

为什么需要这个：填空题的「参考答案」是直接展示给学生的，
如果参考实现本身有 bug，学生做对了反而会被判错、或者学到错的写法。
排序题这种多分支 + 双层循环的代码，光靠人眼推演很容易漏。

用法：python tools/asm_ref_check.py
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.asm_tasks import ASM_TASKS  # noqa: E402


def run(lines, data, size, base=1000, max_steps=300000):
    """极简 x86 子集解释器：只支持题库里实际出现的指令。"""
    regs = {r: 0 for r in ("eax", "ebx", "ecx", "edx", "esi", "edi")}
    mem = {base + i * 4: v for i, v in enumerate(data)}
    stack, zf, sf = [], 0, 0
    labels, prog = {}, []
    for raw in lines:
        line = raw.split("//")[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            labels[line[:-1]] = len(prog)
            continue
        prog.append(line)

    def addr(op):
        m = re.fullmatch(r"\[(\w+)([+-]\d+)?\]", op)
        return regs[m.group(1)] + (int(m.group(2)) if m.group(2) else 0)

    def rv(op):
        op = op.strip()
        if op.startswith("["):
            return mem.get(addr(op), 0)
        if op.lower() in regs:
            return regs[op.lower()]
        return size if op == "SIZE" else (base if op == "data" else int(op))

    pc = steps = 0
    while pc < len(prog) and steps < max_steps:
        steps += 1
        m = re.match(r"(\w+)\s*(.*)", prog[pc])
        op = m.group(1).lower()
        args = [a.strip() for a in m.group(2).split(",") if a.strip()]
        pc += 1
        if op == "push":
            stack.append(rv(args[0]))
        elif op == "pop":
            regs[args[0].lower()] = stack.pop()
        elif op == "lea":
            regs[args[0].lower()] = rv(args[1])
        elif op == "mov":
            if args[0].startswith("["):
                mem[addr(args[0])] = rv(args[1])
            else:
                regs[args[0].lower()] = rv(args[1])
        elif op == "add":
            if args[0].startswith("["):
                mem[addr(args[0])] = mem.get(addr(args[0]), 0) + rv(args[1])
            else:
                regs[args[0].lower()] += rv(args[1])
        elif op == "dec":
            regs[args[0].lower()] -= 1
            zf = 1 if regs[args[0].lower()] == 0 else 0
        elif op == "cmp":
            d = rv(args[0]) - rv(args[1])
            zf = 1 if d == 0 else 0
            sf = 1 if d < 0 else 0
        elif op == "loop":
            regs["ecx"] -= 1
            if regs["ecx"] != 0:
                pc = labels[args[0]]
        elif op in ("jz", "je"):
            if zf:
                pc = labels[args[0]]
        elif op in ("jnz", "jne"):
            if not zf:
                pc = labels[args[0]]
        elif op == "jle":
            if zf or sf:
                pc = labels[args[0]]
        elif op == "jge":
            if not sf:
                pc = labels[args[0]]
        elif op == "jmp":
            pc = labels[args[0]]
        else:
            raise RuntimeError(f"模拟器未支持：{prog[pc - 1]}")
    return [mem.get(base + i * 4, 0) for i in range(len(data))], steps


def filled(task):
    out, bi = [], 0
    for part in task["parts"]:
        for line in part["lines"]:
            if "____" in line:
                out.append(task["blanks"][bi]["accept"][0])
                bi += 1
            else:
                out.append(line)
    return out


def check_sorting():
    cases = [
        [5, 2, 9, 1, 7, 3],
        [3, 1, 4, 2, 3, 1],
        [1, 2, 3, 4, 5, 6],
        [6, 5, 4, 3, 2, 1],
        [-2, 8, -5, 0, 3, 1],
    ]
    ok = True
    for key in ("bubble_sort", "selection_sort"):
        task = next(t for t in ASM_TASKS if t["key"] == key)
        code = filled(task)
        print(f"=== {task['title']} ===")
        for src in cases:
            got, _ = run(code, list(src), 6)
            good = got == sorted(src)
            ok &= good
            print(f"  {src} -> {got}  {'✓' if good else '✗'}")
    return ok


def check_labels():
    """accept 里的标签名必须与源码大小写一致（MSVC 的 _asm 标签区分大小写）。"""
    bad = []
    for t in ASM_TASKS:
        labels = {}
        for p in t["parts"]:
            for line in p["lines"]:
                m = re.match(r"\s*(\w+):", line)
                if m:
                    labels[m.group(1).lower()] = m.group(1)
        for b in t["blanks"]:
            for a in b["accept"]:
                for tok in a.split():
                    if tok.lower() in labels and tok != labels[tok.lower()]:
                        bad.append(f"{t['key']}: '{tok}' 应为 '{labels[tok.lower()]}'")
    if bad:
        print("\n=== 标签大小写不一致 ===")
        for x in bad:
            print("  ✗", x)
        return False
    print("\n=== 标签大小写 === 全部一致 ✓")
    return True


if __name__ == "__main__":
    ok = check_sorting() and check_labels()
    print("\n结果:", "全部通过" if ok else "有失败项")
    sys.exit(0 if ok else 1)
