"""自编题（第二批，填空版）：换场景不换知识点。

指令与寄存器严格限定在课程 lab 出现过的范围内：
    mov lea push pop add sub inc dec cmp test shl shr sar xor neg xchg
    loop jmp jcc call
    EAX EBX ECX EDX ESI EDI
不用 imul/idiv、位掩码、rol/ror、cmov/setcc、浮点与字符串指令。
"""

BLANK = "____"

EXTRA_TASKS = [
    {
        "key": "neg_count",
        "title": "统计负数个数",
        "level": "easy",
        "source": "自编 · Lab03 循环遍历",
        "brief": "遍历 data（6 个 int），统计小于 0 的元素个数存进 negCount。"
                 "0 不算负数。期望结果：3。",
        "decls": """#define SIZE 6
int data[SIZE] = { 3, -7, 0, -2, 15, -9 };
int negCount;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "lea     esi, data",
                "mov     ecx, SIZE",
                BLANK,
                "negLoop:",
                "mov     edx, [esi]",
                BLANK,
                BLANK,
                "inc     eax",
                "notNeg:",
                BLANK,
                "loop    negLoop",
                "mov     negCount, eax",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["xor eax, eax"],
             "hint": "计数寄存器先清零。",
             "why": "xor eax, eax —— 计数从 0 开始。不清零就是从垃圾值累加。"},
            {"accept": ["cmp edx, 0"],
             "hint": "把当前元素和 0 比。",
             "why": "cmp edx, 0 —— 和 0 比较，紧接着用有符号跳转判断正负。"},
            {"accept": ["jge notNeg"],
             "hint": "大于等于 0 就跳过计数 —— 这样 0 也被排除了。",
             "why": "jge notNeg：有符号的「大于等于」。"
                    "用 jae 会把负数当成很大的无符号数，结果永远不计数。"},
            {"accept": ["add esi, 4"],
             "hint": "指针前进一个 int。",
             "why": "add esi, 4 —— 一个 int 4 字节。"},
        ],
        "note": "判断「负数」必须用有符号跳转（jl / jge / js）；"
                "用无符号那组会把负数的最高位当成「很大」，逻辑整个反过来。",
    },
    {
        "key": "incr_array",
        "title": "数组元素各加一",
        "level": "easy",
        "source": "自编 · Lab03 指针写回",
        "brief": "把 data 里每个元素加 1 并写回原数组，完成后应变成 { 2, 3, 4, 5, 6 }。",
        "decls": """#define SIZE 5
int data[SIZE] = { 1, 2, 3, 4, 5 };""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "lea     esi, data",
                "mov     ecx, SIZE",
                "incLoop:",
                "mov     eax, [esi]",
                "inc     eax",
                BLANK,
                BLANK,
                "loop    incLoop",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["mov [esi], eax", "mov dword ptr [esi], eax"],
             "hint": "改完的值要送回去，否则数组还是原样。",
             "why": "mov [esi], eax —— 方括号表示写到那个地址。"
                    "只改 EAX 不写回，是这道题最常见的漏项。"},
            {"accept": ["add esi, 4"],
             "hint": "指针走到下一个元素。",
             "why": "add esi, 4 —— 一个 int 4 字节。"},
        ],
        "note": "「读—改—写」三步必须完整：mov 出来、运算、mov 回去。"
                "少最后一步，程序能跑但数组没变。",
    },
    {
        "key": "times3",
        "title": "不用乘法算三倍",
        "level": "medium",
        "source": "自编 · Lab02 移位",
        "brief": "计算 result = value × 3，不许用 imul，只能用移位和加法。value 可能是负数。",
        "decls": "int value, result;",
        "parts": [{
            "label": "",
            "lines": [
                "mov     eax, value",
                BLANK,
                BLANK,
                BLANK,
                "mov     result, eax",
            ],
        }],
        "blanks": [
            {"accept": ["mov edx, eax"],
             "hint": "移位会破坏原值，先留一份。",
             "why": "mov edx, eax —— 把原值备份出来。"
                    "不备份的话，移位之后原始 value 就找不回来了。"},
            {"accept": ["shl eax, 1"],
             "hint": "左移一位 = 乘 2。",
             "why": "shl eax, 1 等于乘以 2。左移不区分符号，负数也成立。"},
            {"accept": ["add eax, edx"],
             "hint": "2 倍再加回 1 倍。",
             "why": "add eax, edx —— 2×value 加上备份的 value，得到 3×value。"},
        ],
        "note": "移位就是乘除 2 的幂。任意常数乘法都能拆成「移位 + 加法」，"
                "这是没有乘法指令时的基本功。",
    },
    {
        "key": "abs_sum",
        "title": "绝对值之和",
        "level": "medium",
        "source": "自编 · Lab04 条件取负",
        "brief": "把 data 每个元素取绝对值后累加，存进 absSum。"
                 "期望：3 + 7 + 2 + 5 + 1 = 18。",
        "decls": """#define SIZE 5
int data[SIZE] = { -3, 7, -2, 5, -1 };
int absSum;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "lea     esi, data",
                "mov     ecx, SIZE",
                BLANK,
                "absLoop:",
                "mov     edx, [esi]",
                "test    edx, edx",
                BLANK,
                "neg     edx",
                "positive:",
                BLANK,
                BLANK,
                "loop    absLoop",
                "mov     absSum, eax",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["xor eax, eax"],
             "hint": "累加器清零。",
             "why": "xor eax, eax —— 累加器从 0 开始。"},
            {"accept": ["jns positive"],
             "hint": "不是负数就跳过取反。",
             "why": "jns positive：SF = 0 表示非负（含 0），直接累加。"
                    "写成 js 就把条件反了，正数会被取反。"},
            {"accept": ["add eax, edx"],
             "hint": "此时 EDX 已经是绝对值，累加。",
             "why": "add eax, edx —— 取反发生在累加之前，所以这里加进去的是绝对值。"},
            {"accept": ["add esi, 4"],
             "hint": "指针往前走一个。",
             "why": "add esi, 4。"},
        ],
        "note": "先决定用哪个值（原值还是取反值），再做累加。"
                "顺序反了就会把负数直接加进去。",
    },
    {
        "key": "sum_until_zero",
        "title": "遇到零就停",
        "level": "medium",
        "source": "自编 · Lab03 提前退出",
        "brief": "从头累加 data，遇到 0 立刻停止（0 本身也不加），存进 sum。"
                 "期望：5 + 3 = 8。",
        "decls": """#define SIZE 6
int data[SIZE] = { 5, 3, 0, 9, 2, 1 };
int sum;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "lea     esi, data",
                "mov     ecx, SIZE",
                BLANK,
                "sumLoop:",
                "mov     edx, [esi]",
                "test    edx, edx",
                BLANK,
                "add     eax, edx",
                BLANK,
                BLANK,
                "finished:",
                "mov     sum, eax",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["xor eax, eax"],
             "hint": "求和之前先清零。",
             "why": "xor eax, eax —— 和从 0 开始。"},
            {"accept": ["jz finished"],
             "hint": "是 0 就直接跳到循环外面。",
             "why": "jz finished —— 跳到结束标签，不再累加也不再 LOOP。"
                    "如果只是跳过 add，后面的数仍会被加进来。"},
            {"accept": ["add esi, 4"],
             "hint": "没遇到 0，指针继续走。",
             "why": "add esi, 4。"},
            {"accept": ["loop sumLoop"],
             "hint": "还有元素就继续。",
             "why": "loop sumLoop —— 正常走到末尾时靠它收尾；"
                    "遇到 0 的那条路径已经从 jz 跳出去了，不会回到这里。"},
        ],
        "note": "提前退出的关键是标签位置：finished 必须在 LOOP 之后，"
                "否则跳出去还会被 LOOP 拉回来。",
    },
    {
        "key": "array_equal",
        "title": "判断两个数组是否相同",
        "level": "hard",
        "source": "自编 · Lab03 + Lab04 双指针",
        "brief": "逐元素比较 a 和 b（各 4 个 int）：全同则 same = 1，"
                 "有一对不同就 same = 0 并立刻结束。本例第 3 个元素不同（2 vs 7），"
                 "期望 same = 0。",
        "decls": """#define SIZE 4
int a[SIZE] = { 3, 8, 2, 9 };
int b[SIZE] = { 3, 8, 7, 9 };
int same;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "push    edi",
                "lea     esi, a",
                BLANK,
                "mov     ecx, SIZE",
                BLANK,
                "sameLoop:",
                "mov     edx, [esi]",
                BLANK,
                "jne     different",
                BLANK,
                "add     edi, 4",
                "loop    sameLoop",
                BLANK,
                "different:",
                "mov     eax, 0",
                "finished:",
                "mov     same, eax",
                "pop     edi",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["lea edi, b"],
             "hint": "第二个指针指向 b。",
             "why": "lea edi, b —— LEA 取的是地址（不是内容），指针要的正是地址。"},
            {"accept": ["mov eax, 1"],
             "hint": "先假定它们相同。",
             "why": "mov eax, 1 —— 先假设相同，发现不同再改成 0。"
                    "反过来的话（先假定不同）要写更多分支。"},
            {"accept": ["cmp edx, [edi]"],
             "hint": "可以直接把寄存器和内存比。",
             "why": "cmp edx, [edi] —— 一条指令完成「取出一个、和另一个比」，"
                    "不用先 mov 再 cmp。"},
            {"accept": ["add esi, 4"],
             "hint": "第一个数组的指针也要跟上。",
             "why": "add esi, 4 —— 两个指针必须同步前进，只动一个就错位了。"},
            {"accept": ["jmp finished"],
             "hint": "全等跑完之后，别掉进「置 0」那段。",
             "why": "jmp finished —— 少了这条，循环正常结束时也会执行 mov eax, 0，"
                    "全等的结果被误判成不同。"},
        ],
        "note": "多出口控制流最容易漏的就是这条 jmp："
                "「出错分支」放在正常路径后面，正常路径必须显式跳过它。",
    },
    {
        "key": "bubble_sort",
        "title": "冒泡排序（升序）",
        "level": "hard",
        "source": "自编 · 排序（Assessment 同型）",
        "brief": "把 data 的 6 个数按升序排好。相邻两个比，前面比后面大就交换，"
                 "每跑一轮最大的会沉到末尾。内层用 LOOP（ECX 归它），"
                 "外层不能再借 ECX，得自己用一个寄存器计数。",
        "decls": """#define SIZE 6
int data[SIZE] = { 5, 2, 9, 1, 7, 3 };""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "push    ebx",
                BLANK,
                "outerLoop:",
                BLANK,
                "mov     ecx, ebx",
                BLANK,
                BLANK,
                "innerLoop:",
                "mov     eax, [esi]",
                "mov     edx, [esi+4]",
                BLANK,
                BLANK,
                "mov     [esi], edx",
                BLANK,
                "noSwap:",
                "add     esi, 4",
                "loop    innerLoop",
                "dec     ebx",
                BLANK,
                "done:",
                "pop     ebx",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["mov ebx, SIZE"],
             "hint": "外层要用一个自己的计数器，装总元素数。",
             "why": "mov ebx, SIZE —— 外层计数。SIZE 是 #define 出来的常量，"
                    "汇编里可以直接当立即数用；换成 const int 就装不进寄存器了。"},
            {"accept": ["lea esi, data"],
             "hint": "每一轮都要从数组开头重新扫。",
             "why": "lea esi, data 放在 outerLoop 里面 —— 指针必须每轮重置回数组头。"
                    "放到循环外面，第二轮就从半路开始了。"},
            {"accept": ["dec ecx"],
             "hint": "内层比外层的次数少一次。",
             "why": "dec ecx：内层要比 EBX-1 次（每轮末尾已经定死一个）。"
                    "少了这一条，内层会多比一次，越界读 [esi+4]。"},
            {"accept": ["jz done"],
             "hint": "ECX 要变成 0 的时候，得先拦住。",
             "why": "jz done —— 拦住 ECX=0 的情况。LOOP 是先减再判，"
                    "进去时 ECX=0 就会减成 42 亿，直接卡死（Lab03 那个坑）。"},
            {"accept": ["cmp eax, edx"],
             "hint": "比相邻两个，前面的在 EAX。",
             "why": "cmp eax, edx —— 拿前一个和后一个比。"},
            {"accept": ["jle noSwap"],
             "hint": "已经有序就别换。",
             "why": "jle noSwap：前 <= 后本来就是升序，跳过交换。"
                    "写成 jge 就变成降序；用 jbe（无符号）负数会判错。"},
            {"accept": ["mov [esi+4], eax"],
             "hint": "交换的另一半 —— 前一行已经把小的写到前面了。",
             "why": "mov [esi+4], eax —— 把大的放到后一个位置。"
                    "两条 mov 才构成完整交换，只写一条等于把后一个覆盖两次。"},
            {"accept": ["jnz outerLoop", "jg outerLoop"],
             "hint": "外层还有轮次就再来一遍。",
             "why": "jnz outerLoop —— EBX 减到 0 就停。外层不能写 loop，"
                    "因为 ECX 已经被内层占用了。"},
        ],
        "note": "双层循环的分工：ECX 交给内层 LOOP，外层用 EBX 自己 dec + jnz；"
                "指针 lea 必须放在外层循环体内，每轮重置。"
                "另外 dec ecx 之后一定要先 jz 拦一下 —— ECX 为 0 时 LOOP 会先减再判，"
                "直接绕成 42 亿次。",
    },
    {
        "key": "selection_sort",
        "title": "选择排序（升序）",
        "level": "hard",
        "source": "自编 · 排序（Assessment 同型）",
        "brief": "每一轮在「还没排好的部分」里找出最小值，和这部分的第一位交换。"
                 "注意要同时维护两样东西：最小值本身，以及它在哪里。",
        "decls": """#define SIZE 6
int data[SIZE] = { 5, 2, 9, 1, 7, 3 };""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "push    edi",
                "push    ebx",
                BLANK,
                BLANK,
                "outerLoop:",
                BLANK,
                "mov     eax, [esi]",
                "mov     ecx, ebx",
                BLANK,
                BLANK,
                "mov     edx, esi",
                "scanLoop:",
                "add     edx, 4",
                BLANK,
                BLANK,
                "mov     eax, [edx]",
                BLANK,
                "notSmaller:",
                "loop    scanLoop",
                "placeIt:",
                "mov     edx, [esi]",
                "mov     [esi], eax",
                "mov     [edi], edx",
                "add     esi, 4",
                "dec     ebx",
                BLANK,
                "done:",
                "pop     ebx",
                "pop     edi",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["lea esi, data"],
             "hint": "ESI 指向本轮要填的位置，一开始是数组头。",
             "why": "lea esi, data —— ESI 是「本轮待填位置」，从数组头开始，"
                    "每轮往后挪一个。"},
            {"accept": ["mov ebx, SIZE"],
             "hint": "外层计数器装总元素数。",
             "why": "mov ebx, SIZE —— 剩余待排的元素个数，每轮减一。"},
            {"accept": ["mov edi, esi"],
             "hint": "先假定当前位置就是最小值的位置。",
             "why": "mov edi, esi —— 每轮开始时把「最小值的位置」重置到本轮开头。"
                    "漏了这条，EDI 会残留上一轮的位置，最后一交换就错位。"},
            {"accept": ["dec ecx"],
             "hint": "剩下要比几个？",
             "why": "dec ecx：本轮还有 EBX 个元素，其中第一个已经当作候选，"
                    "所以只需要再比 EBX-1 次。"},
            {"accept": ["jz placeIt"],
             "hint": "只剩一个元素时不用扫，直接放。",
             "why": "jz placeIt —— ECX=0 时跳过扫描。"
                    "不拦的话 LOOP 会把 ECX 减成 42 亿（Lab03 的坑）。"},
            {"accept": ["cmp [edx], eax", "cmp dword ptr [edx], eax"],
             "hint": "可以直接拿内存和寄存器比。",
             "why": "cmp [edx], eax —— 方括号表示取那个地址里的值。"
                    "写成 cmp edx, eax 比的就是指针地址本身，永远比不出结果。"
                    "若报 improper operand type，改成 cmp dword ptr [edx], eax。"},
            {"accept": ["jge notSmaller"],
             "hint": "不小于当前最小值，就别动。",
             "why": "jge notSmaller：大于等于就跳过。注意方向 —— 这里问的是"
                    "「有没有变小」，和冒泡那条正好相反。"},
            {"accept": ["mov edi, edx"],
             "hint": "只更新数值不够，位置也得跟上。",
             "why": "mov edi, edx —— 记下新最小值的位置。"
                    "只写 mov eax,[edx] 而不写这条，数值更新了、位置还是老的，"
                    "最后交换会换错元素。"},
            {"accept": ["jnz outerLoop", "jg outerLoop"],
             "hint": "还有元素没排好就继续。",
             "why": "jnz outerLoop —— 外层用 EBX 计数；ECX 归内层，不能拿来数外层。"},
        ],
        "note": "选择排序每轮做两件事：找最小值（EAX 记数值、EDI 记位置），"
                "然后和本轮开头交换一次。交换次数比冒泡少得多，但比较次数一样。",
    },
]

