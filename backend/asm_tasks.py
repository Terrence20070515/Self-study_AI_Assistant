"""CSI101 汇编训练题库。

口径完全按课程 lab 来：x86 · Visual Studio 的 MSVC 内联汇编（_asm 块）·
数据一律在 C++ 侧声明、汇编里按变量名引用（内联汇编不能自己定义数据）。
题目从 Lab01–Lab04 的 Task 提炼，覆盖：CMP/Jcc、SHR/SAR/CL、LOOP/TEST、
栈参数调用、指针写回。

学生要**手打**整段汇编，不是填空 —— 所以每题都给：
  decls     C++ 侧已经声明好的变量（直接可用，不用自己写）
  starter   编辑器里的初始骨架
  hints     卡住时按需展开的提示（分条，可以只看第一条）
  reference 参考实现（提交后才给看）
  checklist 判分要点，逐条核对，避免"跑通就算对"
"""

ASM_TASKS = [
    {
        "key": "stack_sort2",
        "title": "栈顶两数降序",
        "level": "easy",
        "lab": "Assessment · 栈操作",
        "brief": "栈顶已经压了两个数。用 pop 把它们取到 EAX / EBX，比较后按降序放回栈 "
                 "—— 大的那个在栈顶（最后 push 的在顶上）。"
                 "不交换和交换两条路径，最后都要走到那两条 push。",
        "decls": "int a, b;\n// 进入 _asm 之前：push a / push b 已经把两个数放到栈顶",
        "starter": "_asm {\n    \n}",
        "hints": [
            "pop 的顺序决定谁是谁：先 pop 到 EAX 拿到的是原来的栈顶。",
            "cmp eax, ebx 之后，jge 表示「EAX 已经不小于 EBX」，那就跳过交换。",
            "三个 mov 才能完成交换，需要一个第三个寄存器暂存 —— 直接用 ECX。",
            "push 的顺序反过来想：谁想留在栈顶，谁就最后 push。",
            "交换分支可以 jmp 汇合，但更省事的写法是让两条 push 放在标签之后，"
            "两条路径自然都会经过。",
        ],
        "reference": (
            "_asm {\n"
            "    pop     eax               // 原来的栈顶\n"
            "    pop     ebx               // 第二个\n"
            "    cmp     eax, ebx\n"
            "    jge     done              // eax >= ebx，已经是降序，不用换\n"
            "    mov     ecx, eax          // 交换 eax / ebx\n"
            "    mov     eax, ebx\n"
            "    mov     ebx, ecx\n"
            "done:\n"
            "    push    ebx               // 小的先入栈\n"
            "    push    eax               // 大的后入栈 -> 落在栈顶\n"
            "}"
        ),
        "checklist": [
            "pop 到 EAX / EBX 的顺序与题目一致",
            "用有符号比较（cmp + jge / jl），不是 jae / jb",
            "交换用三个 mov（或用 xchg 一步完成）",
            "最后 push 的顺序：先小后大，大值落在栈顶",
            "不管走不走交换分支，两条 push 都会执行到",
        ],
    },
    {
        "key": "max3",
        "title": "三个数取最大",
        "level": "easy",
        "lab": "Lab 01 · Task 1",
        "brief": "在 _asm 块里比较 first / second / third，把最大的那个存进 largest。"
                 "输入可能是负数。",
        "decls": "int first, second, third, largest;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "用「当前最大值」模式：EAX 存目前见过最大的，每来一个新候选就比一次。三个数比两次就够。",
            "形状是 cmp eax, second / jge 跳过 / mov eax, second / 跳过:",
            "必须用有符号跳转（JG / JGE）。用 JA / JAE 会把 -5 判成比 -20 小。",
            "标签后面必须跟一条指令，不能悬在块尾。",
        ],
        "reference": (
            "_asm {\n"
            "    mov     eax, first\n"
            "    cmp     eax, second\n"
            "    jge     checkThird\n"
            "    mov     eax, second\n"
            "checkThird:\n"
            "    cmp     eax, third\n"
            "    jge     haveMax\n"
            "    mov     eax, third\n"
            "haveMax:\n"
            "    mov     largest, eax\n"
            "}"
        ),
        "checklist": [
            "两次比较（不是三次），用 running-maximum 模式",
            "使用有符号条件跳转 jge / jg（不是 jae / ja）",
            "最终结果写回 largest",
            "每个标签后都有指令",
        ],
    },
    {
        "key": "count_up",
        "title": "循环直到相等",
        "level": "easy",
        "lab": "Lab 01 · Task 2",
        "brief": "从 cur 开始每次加 1，直到 cur 等于 target 为止；"
                 "把一共加了多少次记进 steps，最后把 cur 也更新回变量。",
        "decls": "int cur, target, steps;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "比较要放在循环体开头：相等就跳出去，不相等才自增。",
            "计数用 INC（比 ADD reg, 1 短一个字节，也是 lab 里要求的形式）。",
            "循环末尾需要一条 jmp 跳回比较处 —— 这不是 LOOP 指令，LOOP 只能按 ECX 倒数。",
            "别把 cur 只留在寄存器里：循环结束后要 mov 回变量。",
        ],
        "reference": (
            "_asm {\n"
            "    mov     eax, cur\n"
            "    mov     ebx, target\n"
            "    xor     ecx, ecx          // steps = 0\n"
            "compareLoop:\n"
            "    cmp     eax, ebx\n"
            "    je      finished\n"
            "    inc     eax\n"
            "    inc     ecx\n"
            "    jmp     compareLoop\n"
            "finished:\n"
            "    mov     cur, eax\n"
            "    mov     steps, ecx\n"
            "}"
        ),
        "checklist": [
            "循环条件在体首判断，相等才退出",
            "计数用 inc（不是 add reg,1 之外的自创写法）",
            "有跳回比较处的 jmp",
            "cur 与 steps 都写回了变量",
        ],
    },
    {
        "key": "shift_cl",
        "title": "用 CL 做变量移位",
        "level": "medium",
        "lab": "Lab 02 · Task 1",
        "brief": "把 value 右移 count 位：算术移位的结果存 arithmetic，逻辑移位的结果存 logical。"
                 "count 是变量，不是常量。",
        "decls": "int value, count, arithmetic, logical;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "移位次数不是常量时，只能放在 CL 里 —— 指令编码没有别的选择。",
            "不能直接把字节寄存器从 32 位变量里取出来：先 mov ecx, count，CL 就是 ECX 的低字节。",
            "两次移位之间要把 value 重新装回 EAX，否则第二次是在移位后的结果上再移。",
        ],
        "reference": (
            "_asm {\n"
            "    mov     ecx, count\n"
            "    mov     eax, value\n"
            "    sar     eax, cl           // 算术右移：符号位复制下来\n"
            "    mov     arithmetic, eax\n"
            "    mov     eax, value\n"
            "    shr     eax, cl           // 逻辑右移：高位补 0\n"
            "    mov     logical, eax\n"
            "}"
        ),
        "checklist": [
            "移位次数来自 CL（先 mov ecx, count）",
            "算术用 sar、逻辑用 shr，两者没搞反",
            "每次移位前都重新把 value 装进 EAX",
        ],
    },
    {
        "key": "count_ones",
        "title": "数 1 的位数",
        "level": "medium",
        "lab": "Lab 02 · Task 2",
        "brief": "统计 value 的 32 位里有多少位是 1，结果存进 ones。"
                 "验证：-1 得 32，0 得 0，255 得 8，-32 得 27。",
        "decls": "unsigned int value;\nint ones;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "shr 一次，最低位就被推进进位标志 CF；JNC 跳过「加一」那步。",
            "循环 32 次，用 LOOP 最省事（ECX 自动倒数）。",
            "别在循环里破坏 ECX —— LOOP 靠它计数。",
            "如果用 EBX 存计数，记得 push / pop（callee-saved）。",
        ],
        "reference": (
            "_asm {\n"
            "    xor     eax, eax          // 计数\n"
            "    mov     edx, value\n"
            "    mov     ecx, 32\n"
            "countLoop:\n"
            "    shr     edx, 1            // 最低位进 CF\n"
            "    jnc     skip\n"
            "    inc     eax\n"
            "skip:\n"
            "    loop    countLoop\n"
            "    mov     ones, eax\n"
            "}"
        ),
        "checklist": [
            "用 shr 把最低位送进 CF，再看 CF（jnc / jc / adc 皆可）",
            "恰好循环 32 次",
            "循环控制寄存器（ECX）在体内没被破坏",
            "结果写回 ones",
        ],
    },
    {
        "key": "even_sum",
        "title": "偶数求和与计数",
        "level": "medium",
        "lab": "Lab 03 · Task 1",
        "brief": "用 LOOP 走完 data 数组（5 个 int），只把偶数累加进 evenSum，"
                 "同时用 evenCount 记下有几个偶数。期望：3 个偶数，和 28。",
        "decls": "#define SIZE 5\nint data[SIZE] = { 4, 8, 15, 16, 23 };\nint evenCount, evenSum;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "判断奇偶看最低位，用 test edx, 1 —— 不是 cmp。TEST 只留标志位，正好问「这一位是不是 1」。",
            "给了寄存器分工就先写下来：ESI 指针、EAX 和、EBX 个数、EDX 当前元素、ECX 计数器。",
            "ESI 和 EBX 都属于自己要保护的寄存器：进来 push，出去按反序 pop。",
            "指针每次前进 4 字节（一个 int）。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    push    ebx\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "    xor     eax, eax          // sum\n"
            "    xor     ebx, ebx          // count\n"
            "evenLoop:\n"
            "    mov     edx, [esi]\n"
            "    test    edx, 1\n"
            "    jnz     skipEven          // 最低位是 1 -> 奇数\n"
            "    add     eax, edx\n"
            "    inc     ebx\n"
            "skipEven:\n"
            "    add     esi, 4\n"
            "    loop    evenLoop\n"
            "    mov     evenSum, eax\n"
            "    mov     evenCount, ebx\n"
            "    pop     ebx\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "用 test reg, 1 判奇偶（不是 cmp）",
            "ESI 与 EBX 都 push 了，并按反序 pop",
            "指针每次 +4",
            "和与个数分别写回 evenSum / evenCount",
        ],
    },
    {
        "key": "min_max_pass",
        "title": "一趟找出最大和最小",
        "level": "hard",
        "lab": "Lab 03 · Task 2",
        "brief": "只走一遍数组，同时求出最大值和最小值，分别存进 largest / smallest。"
                 "不许走两遍。",
        "decls": "#define SIZE 5\nint data[SIZE] = { 4, 8, 15, 16, 23 };\nint largest, smallest;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "先把第一个元素同时当成最大值和最小值，然后从第二个开始比 —— 这样循环次数少一次。",
            "循环体里两次比较：比当前最大大就换最大，比当前最小小就换最小。",
            "两次比较都要用有符号跳转。",
            "用 EBX 装当前元素的话，EBX 也要 push / pop。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    push    ebx\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "    dec     ecx               // 第一个元素已经处理\n"
            "    mov     eax, [esi]        // largest\n"
            "    mov     edx, [esi]        // smallest\n"
            "    add     esi, 4\n"
            "scanLoop:\n"
            "    mov     ebx, [esi]\n"
            "    cmp     ebx, eax\n"
            "    jle     notLarger\n"
            "    mov     eax, ebx\n"
            "notLarger:\n"
            "    cmp     ebx, edx\n"
            "    jge     notSmaller\n"
            "    mov     edx, ebx\n"
            "notSmaller:\n"
            "    add     esi, 4\n"
            "    loop    scanLoop\n"
            "    mov     largest, eax\n"
            "    mov     smallest, edx\n"
            "    pop     ebx\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "只用一个循环（不是两趟）",
            "最大值与最小值分别用两个寄存器维护",
            "两次比较都用有符号跳转",
            "用到的 callee-saved 寄存器都恢复了",
        ],
    },
    {
        "key": "max_of_3_fn",
        "title": "带三个参数的函数",
        "level": "hard",
        "lab": "Lab 04 · Task 1",
        "brief": "用 _asm 写 maxOf3(a, b, c) 的函数体（结果写进 result），"
                 "再在另一个 _asm 块里手动压栈调用它，把返回值存进 answer。",
        "decls": "int answer;\nint a = 10, b = 3, c = 25;\n\nint maxOf3(int a, int b, int c)\n{\n    int result;\n    _asm {\n        // 第一段：函数体\n    }\n    return result;\n}",
        "starter": "// 1) 先写 maxOf3 的函数体：\n_asm {\n    \n}\n\n// 2) 再写调用处（在另一个 _asm 块里）：\n_asm {\n    \n}",
        "hints": [
            "函数体里照搬 Lab01 的 running maximum：EAX / ECX / EDX 都空着，不需要 push。",
            "调用处从右往左压：push c，push b，push a。",
            "三个参数意味着 add esp, 12 —— 这是这个 lab 里最常见的错。",
            "第三个参数虽然在 [ebp+16]，但你还是写 c，偏移编译器替你算。",
        ],
        "reference": (
            "// 函数体\n"
            "_asm {\n"
            "    mov     eax, a\n"
            "    cmp     eax, b\n"
            "    jge     checkC\n"
            "    mov     eax, b\n"
            "checkC:\n"
            "    cmp     eax, c\n"
            "    jge     haveMax\n"
            "    mov     eax, c\n"
            "haveMax:\n"
            "    mov     result, eax\n"
            "}\n\n"
            "// 调用处\n"
            "_asm {\n"
            "    push    c                 // 第三个参数先压\n"
            "    push    b\n"
            "    push    a                 // 第一个参数最后压\n"
            "    call    maxOf3\n"
            "    add     esp, 12           // 三个参数\n"
            "    mov     answer, eax\n"
            "}"
        ),
        "checklist": [
            "压栈顺序是 c、b、a（右到左）",
            "调用后 add esp, 12（不是 8）",
            "函数体用两次比较求最大值",
            "返回值从 EAX 取回并存进 answer",
        ],
    },
    {
        "key": "min_max_ptr",
        "title": "用指针返回两个结果",
        "level": "hard",
        "lab": "Lab 04 · Task 2",
        "brief": "实现 minMax(a, b, lo, hi)：把较小的写进 *lo，较大的写进 *hi。"
                 "EAX 只能带回一个值，所以另一个必须通过指针写出去。",
        "decls": "int lo = 0, hi = 0;\n\nvoid minMax(int a, int b, int* lo, int* hi)\n{\n    _asm {\n        \n    }\n}",
        "starter": "_asm {\n    \n}",
        "hints": [
            "先 mov eax, a / mov edx, b，再用 cmp 比一次。",
            "如果顺序反了，xchg eax, edx 一条指令就能交换。",
            "写回用方括号：mov [ebx], eax 才是「写到那个地址」，没有方括号只是改指针本身。",
            "用了 EBX 就要 push / pop，而且 pop 必须在所有分支汇合之后。",
        ],
        "reference": (
            "_asm {\n"
            "    push    ebx\n"
            "    mov     eax, a\n"
            "    mov     edx, b\n"
            "    cmp     eax, edx\n"
            "    jle     inOrder           // a <= b，已经是有序的\n"
            "    xchg    eax, edx\n"
            "inOrder:                      // eax = 小的，edx = 大的\n"
            "    mov     ebx, lo\n"
            "    mov     [ebx], eax        // *lo = 小的\n"
            "    mov     ebx, hi\n"
            "    mov     [ebx], edx        // *hi = 大的\n"
            "    pop     ebx\n"
            "}"
        ),
        "checklist": [
            "用方括号写回（mov [ebx], eax），不是改指针",
            "两个指针参数都写了",
            "用了 EBX 并且恢复",
            "相等的情况（a == b）也对",
        ],
    },
]

ASM_TASK_MAP = {t["key"]: t for t in ASM_TASKS}


def public_task(t: dict) -> dict:
    """给前端的版本：去掉参考答案（提交后才给看）。"""
    return {k: v for k, v in t.items() if k != "reference"}
