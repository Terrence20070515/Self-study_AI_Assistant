"""CSI101 汇编训练题库 · 填空版。

形式对齐课程 Assessment：给完整的代码骨架，只挖掉关键的那几行，
学生填的是「这一行该写什么」，不是从零敲一整段。
理由：填空能一眼核对（错在哪一行、对没对），手敲整段反而没法验证。

数据结构：
    parts   一个或多个代码片段（每段有 label），行内用 ____ 占位
    blanks  按 ____ 出现的顺序一一对应，每个空有
              accept  可接受答案（归一化后比较，空白/大小写/逗号空格都忽略）
              hint    卡住时的提示
              why     填错时的解释，也用于提交后的逐条复盘
    note    全对后给出的机制说明

允许的指令严格限定在课程 lab 出现过的范围内（见 README 的安全集）。
"""

BLANK = "____"

ASM_TASKS = [
    {
        "key": "stack_sort2",
        "title": "栈顶两数降序",
        "level": "easy",
        "source": "Assessment · 栈操作",
        "brief": "栈顶已经压了两个数。把它们取到 EAX / EBX，比较后按降序放回栈 "
                 "—— 大的那个要在栈顶。不交换和交换两条路径，最后都要走到那两条 push。",
        "decls": """int a, b;
// 进入 _asm 之前：push a / push b 已经把两个数放到栈顶""",
        "parts": [{
            "label": "",
            "lines": [
                "pop     eax",
                "pop     ebx",
                BLANK,
                BLANK,
                "mov     ecx, eax",
                "mov     eax, ebx",
                BLANK,
                "done:",
                "push    ebx",
                "push    eax",
            ],
        }],
        "blanks": [
            {"accept": ["cmp eax, ebx"],
             "hint": "比较两个寄存器，不用改任何值。",
             "why": "第 3 行只是比较：cmp eax, ebx。它只设标志位，不动寄存器。"},
            {"accept": ["jge done"],
             "hint": "EAX 已经不小于 EBX 时要跳过交换。",
             "why": "要写成 jge done —— 有符号的「大于等于」才跳过交换。"
                    "用 ja 会在负数时判错。"},
            {"accept": ["mov ebx, ecx"],
             "hint": "交换的第三步：把暂存的值放回去。",
             "why": "交换要三条 mov：先 mov ecx,eax 暂存，再 mov eax,ebx，"
                    "最后 mov ebx,ecx 把暂存值放回 ebx。"},
        ],
        "note": "关键在于 push 的顺序：jge 保证了交换后一定有 eax >= ebx，"
                "所以先 push ebx（小的）、再 push eax（大的），大值才落在栈顶。",
    },
    {
        "key": "max3",
        "title": "三个数取最大",
        "level": "easy",
        "source": "Lab 01 · Task 1",
        "brief": "用「当前最大值」模式比较 first / second / third，把最大的存进 largest。"
                 "输入可能是负数。",
        "decls": "int first, second, third, largest;",
        "parts": [{
            "label": "",
            "lines": [
                "mov     eax, first",
                "cmp     eax, second",
                BLANK,
                "mov     eax, second",
                "checkThird:",
                BLANK,
                "jge     haveMax",
                BLANK,
                "haveMax:",
                "mov     largest, eax",
            ],
        }],
        "blanks": [
            {"accept": ["jge checkthird", "jg checkthird"],
             "hint": "EAX 已经 >= second 就不用覆盖它。",
             "why": "jge checkThird：跳过「把 second 装进 eax」那一步。"
                    "必须用有符号跳转 —— 用 jae 会把负数当大数。"},
            {"accept": ["cmp eax, third"],
             "hint": "第二次比较：当前最大值和第三个候选。",
             "why": "cmp eax, third —— running max 的第二轮，拿当前最大值比新候选。"},
            {"accept": ["mov eax, third"],
             "hint": "第三个更大时，把它变成新的最大值。",
             "why": "mov eax, third —— 只有 jge 没跳（即 third 更大）时才会执行到这里。"},
        ],
        "note": "running-maximum：EAX 先当临时最大值，依次和每个候选比一次。"
                "三个数只要比两次，不是三次。",
    },
    {
        "key": "count_up",
        "title": "循环直到相等",
        "level": "easy",
        "source": "Lab 01 · Task 2",
        "brief": "从 cur 开始每次加 1，直到等于 target；把加的次数记进 steps，"
                 "cur 也要更新回变量。",
        "decls": "int cur, target, steps;",
        "parts": [{
            "label": "",
            "lines": [
                "mov     eax, cur",
                "mov     ebx, target",
                "xor     ecx, ecx",
                "compareLoop:",
                BLANK,
                "je      finished",
                "inc     eax",
                BLANK,
                BLANK,
                "finished:",
                "mov     cur, eax",
                "mov     steps, ecx",
            ],
        }],
        "blanks": [
            {"accept": ["cmp eax, ebx"],
             "hint": "循环条件：当前值和目标值比较。",
             "why": "cmp eax, ebx，紧接着 je finished 表示「相等就出去」。"},
            {"accept": ["inc ecx"],
             "hint": "计一次步数。",
             "why": "inc ecx 统计加了几次。用 inc 比 add ecx,1 短。"},
            {"accept": ["jmp compareloop"],
             "hint": "这一轮没相等，回到上面再比。",
             "why": "jmp compareLoop 跳回比较处。这不是 LOOP 指令 —— "
                    "LOOP 只按 ECX 倒数，这里不能用。"},
        ],
        "note": "条件判断放在循环体开头，跳出去之后才写回变量。"
                "这个结构就是 while (cur != target) 的汇编版。",
    },
    {
        "key": "shift_cl",
        "title": "用 CL 做变量移位",
        "level": "medium",
        "source": "Lab 02 · Task 1",
        "brief": "把 value 右移 count 位（count 是变量不是常量）："
                 "算术移位结果存 arithmetic，逻辑移位结果存 logical。",
        "decls": "int value, count, arithmetic, logical;",
        "parts": [{
            "label": "",
            "lines": [
                BLANK,
                "mov     eax, value",
                BLANK,
                "mov     arithmetic, eax",
                "mov     eax, value",
                BLANK,
                "mov     logical, eax",
            ],
        }],
        "blanks": [
            {"accept": ["mov ecx, count"],
             "hint": "移位次数要放进 CL，而 CL 是 ECX 的低字节。",
             "why": "mov ecx, count —— 不能直接给 CL 赋值。先装 ECX，CL 就是它的低 8 位。"
                    "移位次数不是常量时，也只能放在 CL 里。"},
            {"accept": ["sar eax, cl"],
             "hint": "算术右移：符号位要复制下来。",
             "why": "sar eax, cl 是算术右移，负数移位后仍然是负数。"
                    "用 shr 会补 0，把 -32 变成大正数。"},
            {"accept": ["shr eax, cl"],
             "hint": "逻辑右移：高位一律补 0。",
             "why": "shr eax, cl 是逻辑右移。同一份 value、同一个次数，"
                    "它和 sar 的结果只有在负数时才不同 —— 这正是这个 lab 的重点。"},
        ],
        "note": "SHR 与 SAR 的分歧只出现在负数上；正数时两者一样，"
                "所以这个 bug 特别容易漏测。",
    },
    {
        "key": "count_ones",
        "title": "数 1 的位数",
        "level": "medium",
        "source": "Lab 02 · Task 2",
        "brief": "统计 value 的 32 位里有多少位是 1，存进 ones。"
                 "自检：-1 得 32，0 得 0，255 得 8，-32 得 27。",
        "decls": "unsigned int value;\nint ones;",
        "parts": [{
            "label": "",
            "lines": [
                "xor     eax, eax",
                "mov     edx, value",
                "mov     ecx, 32",
                "countLoop:",
                BLANK,
                BLANK,
                "inc     eax",
                "skip:",
                BLANK,
                "mov     ones, eax",
            ],
        }],
        "blanks": [
            {"accept": ["shr edx, 1"],
             "hint": "把最低位挤出去，它会落到进位标志里。",
             "why": "shr edx, 1 —— 右移一位，最低位被推进 CF。"
                    "这里必须用 shr（逻辑），不能用 sar。"},
            {"accept": ["jnc skip"],
             "hint": "刚才那一位是 0 就跳过计数。",
             "why": "jnc skip：CF = 0 表示这一位是 0，不计数。"
                    "写 jc 就把逻辑反了。"},
            {"accept": ["loop countloop"],
             "hint": "32 次走完。",
             "why": "loop countLoop 一次完成「ECX 减一 + 非零就跳」。"
                    "注意它不改变标志位，所以可以和上面的 jnc 共存。"},
        ],
        "note": "这个模式是「移位把位送进 CF，再看 CF」——"
                "凡是逐位检查的题，都是这个骨架。",
    },
    {
        "key": "even_sum",
        "title": "偶数求和与计数",
        "level": "medium",
        "source": "Lab 03 · Task 1",
        "brief": "用 LOOP 走完 data（5 个 int），只累加偶数并计数。"
                 "期望：3 个偶数，和 28。",
        "decls": """#define SIZE 5
int data[SIZE] = { 4, 8, 15, 16, 23 };
int evenCount, evenSum;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "push    ebx",
                "lea     esi, data",
                "mov     ecx, SIZE",
                "xor     eax, eax",
                "xor     ebx, ebx",
                "evenLoop:",
                "mov     edx, [esi]",
                BLANK,
                BLANK,
                "add     eax, edx",
                "inc     ebx",
                "skipEven:",
                BLANK,
                "loop    evenLoop",
                "mov     evenSum, eax",
                "mov     evenCount, ebx",
                "pop     ebx",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["test edx, 1"],
             "hint": "只看最低位，不改值 —— 这不是比较大小。",
             "why": "test edx, 1 做按位与，只留标志位。"
                    "这里不该用 cmp —— cmp 是比大小，test 才是问某一位是否为 1。"},
            {"accept": ["jnz skipeven"],
             "hint": "最低位是 1 说明是奇数，跳过累加。",
             "why": "jnz skipEven：结果为 1（奇数）就跳过。"
                    "也可写 jne，但 jnz 更贴切 —— 问的是「非零」而非「不等」。"},
            {"accept": ["add esi, 4"],
             "hint": "指针前进一个 int。",
             "why": "add esi, 4 —— 一个 int 是 4 字节，不是 1。"},
        ],
        "note": "寄存器分工先定好：ESI 指针、EAX 和、EBX 个数、EDX 当前元素、ECX 计数。"
                "ESI 和 EBX 都是被调用方要保护的，所以 push 进来、反序 pop 出去。",
    },
    {
        "key": "min_max_pass",
        "title": "一趟找出最大和最小",
        "level": "hard",
        "source": "Lab 03 · Task 2",
        "brief": "只走一遍数组，同时求出最大值和最小值，存进 largest / smallest。不许走两遍。",
        "decls": """#define SIZE 5
int data[SIZE] = { 4, 8, 15, 16, 23 };
int largest, smallest;""",
        "parts": [{
            "label": "",
            "lines": [
                "push    esi",
                "push    ebx",
                "lea     esi, data",
                "mov     ecx, SIZE",
                "dec     ecx",
                "mov     eax, [esi]",
                "mov     edx, [esi]",
                "add     esi, 4",
                "scanLoop:",
                "mov     ebx, [esi]",
                "cmp     ebx, eax",
                BLANK,
                "mov     eax, ebx",
                "notLarger:",
                BLANK,
                BLANK,
                "mov     edx, ebx",
                "notSmaller:",
                "add     esi, 4",
                "loop    scanLoop",
                "mov     largest, eax",
                "mov     smallest, edx",
                "pop     ebx",
                "pop     esi",
            ],
        }],
        "blanks": [
            {"accept": ["jle notlarger"],
             "hint": "不比当前最大值大，就跳过更新。",
             "why": "jle notLarger —— 有符号的「小于等于」。"
                    "用 jbe 判断负数时会错。"},
            {"accept": ["cmp ebx, edx"],
             "hint": "同一趟里，再和当前最小值比一次。",
             "why": "cmp ebx, edx —— EDX 维护最小值，所以在同一个循环体里比第二次。"},
            {"accept": ["jge notsmaller"],
             "hint": "不比当前最小值小，就跳过。",
             "why": "jge notSmaller —— 大于等于最小值就不更新。"
                    "注意方向：这里是「没变小就跳过」，和上面那条相反。"},
        ],
        "note": "第一个元素同时当最大和最小，所以循环从第二个开始（dec ecx）。"
                "一个循环、两次比较、两个寄存器各自维护 —— 这就是「一趟」。",
    },
    {
        "key": "max_of_3_fn",
        "title": "带三个参数的函数",
        "level": "hard",
        "source": "Lab 04 · Task 1",
        "brief": "补完 maxOf3 的函数体，以及调用处：调用方手动压三个参数，"
                 "调用后自己清栈。",
        "decls": """int answer;
int a = 10, b = 3, c = 25;

int maxOf3(int a, int b, int c)
{
    int result;
    _asm {
        // 见下方片段一
    }
    return result;
}""",
        "parts": [
            {
                "label": "片段一：函数体内",
                "lines": [
                    "mov     eax, a",
                    "cmp     eax, b",
                    BLANK,
                    "mov     eax, b",
                    "checkC:",
                    "cmp     eax, c",
                    "jge     haveMax",
                    "mov     eax, c",
                    "haveMax:",
                    "mov     result, eax",
                ],
            },
            {
                "label": "片段二：调用处",
                "lines": [
                    "push    c",
                    "push    b",
                    BLANK,
                    "call    maxOf3",
                    BLANK,
                    "mov     answer, eax",
                ],
            },
        ],
        "blanks": [
            {"accept": ["jge checkc", "jg checkc"],
             "hint": "EAX 已经 >= b 就跳到检查 c 那步。",
             "why": "jge checkC —— 有符号比较，且标签是函数体里的 checkC。"},
            {"accept": ["push a"],
             "hint": "三个参数从右往左压，最后压的是第一个参数。",
             "why": "push a —— __cdecl 从右到左：先 c、再 b、最后 a，"
                    "这样 a 离栈顶最近，落在 [ebp+8]。"},
            {"accept": ["add esp, 12"],
             "hint": "三个参数，每个 4 字节，谁清栈？",
             "why": "add esp, 12 —— 三个参数共 12 字节。"
                    "这是这个 lab 最常见的错：写成 8。"},
        ],
        "note": "参数从右往左压，调用方负责清栈（__cdecl）。"
                "函数体内不用管 [ebp+8]，直接写变量名，偏移编译器替你算。",
    },
    {
        "key": "min_max_ptr",
        "title": "用指针返回两个结果",
        "level": "hard",
        "source": "Lab 04 · Task 2",
        "brief": "实现 minMax(a, b, lo, hi)：较小的写进 *lo，较大的写进 *hi。"
                 "EAX 只能带回一个值，所以另一个必须通过指针写出去。",
        "decls": """int lo = 0, hi = 0;

void minMax(int a, int b, int* lo, int* hi)
{
    _asm {
        // 见下方
    }
}""",
        "parts": [{
            "label": "",
            "lines": [
                "push    ebx",
                "mov     eax, a",
                "mov     edx, b",
                "cmp     eax, edx",
                BLANK,
                "xchg    eax, edx",
                "inOrder:",
                "mov     ebx, lo",
                BLANK,
                "mov     ebx, hi",
                BLANK,
                "pop     ebx",
            ],
        }],
        "blanks": [
            {"accept": ["jle inorder"],
             "hint": "a <= b 时已经是有序的，不用交换。",
             "why": "jle inOrder —— 有符号的「小于等于」。"
                    "相等也算有序，所以必须带等号。"},
            {"accept": ["mov [ebx], eax", "mov dword ptr [ebx], eax"],
             "hint": "把较小的写到 lo 指向的地址。",
             "why": "mov [ebx], eax —— 方括号表示「写到那个地址」。"
                    "漏掉方括号就变成改指针本身，*lo 根本没写进去。"},
            {"accept": ["mov [ebx], edx", "mov dword ptr [ebx], edx"],
             "hint": "同一套写法，把较大的写到 hi。",
             "why": "mov [ebx], edx —— EDX 此时是较大的那个。"},
        ],
        "note": "EAX 只能带回一个返回值，第二个结果只能「写出去」——"
                "这就是指针参数的用处。方括号是这里最容易漏的东西。",
    },
]

# 自编题（第二批）在另一个文件，这里合并
from .asm_extra import EXTRA_TASKS  # noqa: E402

ASM_TASKS.extend(EXTRA_TASKS)

ASM_TASK_MAP = {t["key"]: t for t in ASM_TASKS}


def public_task(t: dict) -> dict:
    """给前端的版本：去掉 accept 里的标准答案（提交前不该看到）。"""
    out = {k: v for k, v in t.items() if k != "blanks"}
    out["blanks"] = [{"hint": b.get("hint", ""), "why": b.get("why", "")}
                     for b in t["blanks"]]
    return out


def answer_key(t: dict) -> list:
    """逐空的答案：{accept: [...]}，只在提交后返回给前端。"""
    return [{"accept": b.get("accept", [])} for b in t["blanks"]]
