"""自编题（第二批）：不照搬 lab 原题，但知识点严格限定在课程已覆盖的范围内。

允许的指令只取 lab 里真正出现过的：
    mov / lea / push / pop / add / sub / inc / dec / cmp / test
    shl / shr / sar / sal / xor / neg / xchg / loop / jmp / jcc / call
允许的寄存器：EAX EBX ECX EDX ESI EDI（EBP/ESP 由编译器管，不手写）
内存访问只出现两种：变量名、[ESI] / [EDI] / [EBX] 这种指针间接。

刻意**不用**的：imul/idiv（lab 没让写过）、浮点、字符串指令、
cmov / setcc / rol-ror（讲义有但 lab 没练过）、and/or 做位掩码（容易和英文词混淆，
也无法确认是否讲过）。宁可少一道题，不引入一个没练过的指令。
"""

EXTRA_TASKS = [
    {
        "key": "neg_count",
        "title": "统计负数个数",
        "level": "easy",
        "lab": "自编 · Lab03 循环遍历",
        "brief": "遍历 data 数组（6 个 int），统计其中**小于 0** 的元素有多少个，"
                 "结果存进 negCount。注意 0 不算负数。期望结果：3。",
        "decls": "#define SIZE 6\nint data[SIZE] = { 3, -7, 0, -2, 15, -9 };\nint negCount;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "骨架和 Lab03 的偶数求和一样：ESI 当指针、ECX 倒数、EAX 当计数。",
            "判断「小于 0」要用有符号比较：cmp edx, 0 然后 jl 才计数（用 jb 会把负数当成很大的无符号数）。",
            "0 不算负数 —— cmp 之后用 jge 跳过，等于号就自然被排除了。",
            "ESI 是 callee-saved，进来 push、出去 pop。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "    xor     eax, eax          // 计数归零\n"
            "negLoop:\n"
            "    mov     edx, [esi]\n"
            "    cmp     edx, 0\n"
            "    jge     notNeg            // >= 0，跳过\n"
            "    inc     eax\n"
            "notNeg:\n"
            "    add     esi, 4\n"
            "    loop    negLoop\n"
            "    mov     negCount, eax\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "用 LOOP（或等价的计数循环）走完 6 个元素",
            "判断负数用有符号比较（jl / jge），不是 jb / jae",
            "0 没有被算进负数",
            "ESI 有 push / pop",
        ],
    },
    {
        "key": "incr_array",
        "title": "数组元素各加一",
        "level": "easy",
        "lab": "自编 · Lab03 指针写回",
        "brief": "把 data 数组里每个元素都加 1，**写回原数组**。"
                 "完成后 data 应该变成 { 2, 3, 4, 5, 6 }。",
        "decls": "#define SIZE 5\nint data[SIZE] = { 1, 2, 3, 4, 5 };",
        "starter": "_asm {\n    \n}",
        "hints": [
            "每个元素要做三件事：读出来、加一、写回同一个地址。",
            "写回要用方括号：[esi] 表示那个地址里的内容，mov [esi], eax 才是存回去。",
            "指针每次前进 4 字节（一个 int）。",
            "只改寄存器不写回，数组还是原样 —— 这是最常见的漏项。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "incLoop:\n"
            "    mov     eax, [esi]\n"
            "    inc     eax\n"
            "    mov     [esi], eax        // 写回原地址\n"
            "    add     esi, 4\n"
            "    loop    incLoop\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "每个元素都写回了原数组（mov [esi], ...）",
            "指针每次 +4",
            "循环次数等于 SIZE",
            "ESI 有 push / pop",
        ],
    },
    {
        "key": "times3",
        "title": "不用乘法算三倍",
        "level": "medium",
        "lab": "自编 · Lab02 移位",
        "brief": "计算 result = value × 3，**不许用 imul**，只能用移位和加法。"
                 "value 可能是负数。",
        "decls": "int value, result;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "左移一位等于乘 2：shl eax, 1。",
            "3 倍 = 2 倍 + 1 倍，所以要先把原值留一份。",
            "顺序：先备份原值，再移位，最后把备份加回去。",
            "负值同样成立（左移不区分符号，只要不溢出）。",
        ],
        "reference": (
            "_asm {\n"
            "    mov     eax, value\n"
            "    mov     edx, eax          // 备份原值\n"
            "    shl     eax, 1            // eax = 2 * value\n"
            "    add     eax, edx          // + value = 3 * value\n"
            "    mov     result, eax\n"
            "}"
        ),
        "checklist": [
            "用 shl 实现乘 2（没有用 imul）",
            "移位前备份了原值，最后加回去",
            "结果写回 result",
            "负值也成立（没有误用逻辑右移之类）",
        ],
    },
    {
        "key": "abs_sum",
        "title": "绝对值之和",
        "level": "medium",
        "lab": "自编 · Lab04 条件取负",
        "brief": "把 data 里每个元素取绝对值后累加，结果存进 absSum。"
                 "期望结果：3 + 7 + 2 + 5 + 1 = 18。",
        "decls": "#define SIZE 5\nint data[SIZE] = { -3, 7, -2, 5, -1 };\nint absSum;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "取绝对值：如果是负的，用 neg 取反；非负就原样累加。",
            "用 test edx, edx 之后看符号标志：jns 表示「不是负数」，可以直接累加。",
            "别在累加之后再取负 —— 要先决定用哪个值，再加。",
            "累加寄存器用 EAX，当前元素用 EDX，指针 ESI。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "    xor     eax, eax          // 累加器\n"
            "absLoop:\n"
            "    mov     edx, [esi]\n"
            "    test    edx, edx\n"
            "    jns     positive          // 非负，直接用\n"
            "    neg     edx               // 负数取反\n"
            "positive:\n"
            "    add     eax, edx\n"
            "    add     esi, 4\n"
            "    loop    absLoop\n"
            "    mov     absSum, eax\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "用 test/cmp 判断符号（jns / js）",
            "负数用 neg 取反，非负数不动",
            "取绝对值发生在累加之前",
            "ESI 有 push / pop",
        ],
    },
    {
        "key": "sum_until_zero",
        "title": "遇到零就停",
        "level": "medium",
        "lab": "自编 · Lab03 提前退出",
        "brief": "从头累加 data，**遇到 0 立刻停止**（0 本身也不加），结果存进 sum。"
                 "期望结果：5 + 3 = 8。",
        "decls": "#define SIZE 6\nint data[SIZE] = { 5, 3, 0, 9, 2, 1 };\nint sum;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "判断 0 用 test 或 cmp + jz，命中就跳到循环外面。",
            "跳出去之后不能再 LOOP 回去 —— 所以结束标签要放在循环之后、写回之前。",
            "如果先 add 再判断，0 虽然不影响和，但遇到 0 之后后面的数会被错误地累加进去。",
            "要写的是「先看是不是 0，不是才加」。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    lea     esi, data\n"
            "    mov     ecx, SIZE\n"
            "    xor     eax, eax\n"
            "sumLoop:\n"
            "    mov     edx, [esi]\n"
            "    test    edx, edx\n"
            "    jz      finished          // 遇到 0 直接结束\n"
            "    add     eax, edx\n"
            "    add     esi, 4\n"
            "    loop    sumLoop\n"
            "finished:\n"
            "    mov     sum, eax\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "遇到 0 立即跳出循环（jz / je）",
            "0 之后的元素没有被累加",
            "结束标签位置正确（跳出后不会又 LOOP 回去）",
            "ESI 有 push / pop",
        ],
    },
    {
        "key": "array_equal",
        "title": "判断两个数组是否相同",
        "level": "hard",
        "lab": "自编 · Lab03 + Lab04 双指针",
        "brief": "逐元素比较 a 和 b（各 4 个 int）：完全相同则 same = 1，"
                 "只要有一对不同就 same = 0 并立即结束比较。"
                 "本例第 3 个元素不同（2 vs 7），期望 same = 0。",
        "decls": "#define SIZE 4\nint a[SIZE] = { 3, 8, 2, 9 };\nint b[SIZE] = { 3, 8, 7, 9 };\nint same;",
        "starter": "_asm {\n    \n}",
        "hints": [
            "需要两个指针：ESI 指向 a、EDI 指向 b，两边一起前进。",
            "比较用 mov edx, [esi] 然后 cmp edx, [edi]（可以直接和内存比）。",
            "先假设相同（EAX = 1），发现不同再把它改成 0 并跳出。",
            "全等跑完时要跳过「置 0」那段，否则会被错误地改成 0 —— 加一条 jmp。",
            "ESI 和 EDI 都要保护，pop 的顺序和 push 反过来。",
        ],
        "reference": (
            "_asm {\n"
            "    push    esi\n"
            "    push    edi\n"
            "    lea     esi, a\n"
            "    lea     edi, b\n"
            "    mov     ecx, SIZE\n"
            "    mov     eax, 1            // 先假设相同\n"
            "sameLoop:\n"
            "    mov     edx, [esi]\n"
            "    cmp     edx, [edi]\n"
            "    jne     different\n"
            "    add     esi, 4\n"
            "    add     edi, 4\n"
            "    loop    sameLoop\n"
            "    jmp     finished          // 全等跑完，别掉进 different\n"
            "different:\n"
            "    mov     eax, 0\n"
            "finished:\n"
            "    mov     same, eax\n"
            "    pop     edi\n"
            "    pop     esi\n"
            "}"
        ),
        "checklist": [
            "用两个指针分别走 a 和 b（ESI / EDI）",
            "发现不同立即结束（jne 到置 0 分支）",
            "全等时结果保持 1（没有掉进置 0 的分支）",
            "ESI 与 EDI 都恢复了，且 pop 顺序与 push 相反",
        ],
    },
]
