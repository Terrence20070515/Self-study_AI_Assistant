"""SOE101 SQL 训练题库。

题型仿课程那份 CPT103 SQL Revision：三值逻辑求值、多选概念题、给表写查询。
判分全部在本地做，不调模型 —— 与汇编训练同一套思路：
  · choice  多选/单选：选中集合与答案集合完全一致才算对
  · blank   给 SQL 骨架、挖掉关键字或子句，按 accept 归一化比对
这样「对不对」一眼可见，不用等模型、也不用猜它为什么给这个分。

题目来源：Lab3（建表/外键）、Lab4（SELECT part1）、Lab5（SELECT part2 / JOIN / ORDER BY）、
以及 L1/L2 的数据库基本概念（DDL / DML / DCL、键与约束、数据类型）。
"""
BLANK = "____"

LEVEL_LABEL = {"easy": "易", "medium": "中", "hard": "难"}
KIND_LABEL = {"choice": "选择", "blank": "填空"}

SQL_TASKS = [
    # ---------------- 一、三值逻辑（同资料 Part 1） ----------------
    {
        "key": "tvl_01",
        "kind": "choice",
        "title": "三值逻辑：TRUE AND 比较式",
        "level": "easy",
        "source": "L6 · Missing Information",
        "brief": "把 Unknown 换成 NULL，在 MySQL 里求这个表达式的值。",
        "stem": "TRUE AND (15 > 1)",
        "options": ["TRUE", "FALSE", "NULL"],
        "answer": ["A"],
        "note": "15 > 1 本身是真，TRUE AND TRUE 就是 TRUE。三值逻辑只在有 NULL 参与时才多出第三种值。",
    },
    {
        "key": "tvl_02",
        "kind": "choice",
        "title": "三值逻辑：NULL 参与算术",
        "level": "easy",
        "source": "L6 · Missing Information",
        "brief": "算术运算里出现 NULL，结果是什么？",
        "stem": "NULL + 12",
        "options": ["TRUE", "FALSE", "NULL", "12"],
        "answer": ["C"],
        "note": "NULL 参与任何算术运算，结果一律是 NULL —— 不是 0，也不是 12。",
    },
    {
        "key": "tvl_03",
        "kind": "choice",
        "title": "三值逻辑：OR 短路",
        "level": "medium",
        "source": "L6 · Missing Information",
        "brief": "先算括号里，再看整体。",
        "stem": "(TRUE OR NULL) AND (3 IN (2, 3, 4, 5))",
        "options": ["TRUE", "FALSE", "NULL"],
        "answer": ["A"],
        "note": "TRUE OR NULL = TRUE（OR 只要有一边真就真）；3 IN (2,3,4,5) = TRUE；TRUE AND TRUE = TRUE。",
    },
    {
        "key": "tvl_04",
        "kind": "choice",
        "title": "三值逻辑：LIKE 与 NULL 比较",
        "level": "medium",
        "source": "L6 · Missing Information",
        "brief": "'Bent' 是否以 t 结尾？再看 OR 的另一边。",
        "stem": "'Bent' LIKE '%t' OR NULL <> 5",
        "options": ["TRUE", "FALSE", "NULL"],
        "answer": ["A"],
        "note": "'Bent' LIKE '%t' 为 TRUE，TRUE OR 任何值都是 TRUE —— 包括 TRUE OR NULL。",
    },
    {
        "key": "tvl_05",
        "kind": "choice",
        "title": "三值逻辑：NULL 和 NULL 比较",
        "level": "hard",
        "source": "L6 · Missing Information",
        "brief": "这是最容易凭直觉答错的一题。",
        "stem": "(NULL <> NULL) OR (NULL = NULL)",
        "options": ["TRUE", "FALSE", "NULL"],
        "answer": ["C"],
        "note": "NULL = NULL 与 NULL <> NULL 都不是 TRUE/FALSE，而是 NULL（未知）；NULL OR NULL 仍是 NULL。"
                "判等要用 IS NULL，不能用 =。",
    },
    {
        "key": "tvl_06",
        "kind": "choice",
        "title": "三值逻辑：NULL AND FALSE",
        "level": "hard",
        "source": "L6 · Missing Information",
        "brief": "先化简括号里的算术，再算 AND，最后 NOT。",
        "stem": "NOT (NULL AND (12/3 - 4))",
        "options": ["TRUE", "FALSE", "NULL"],
        "answer": ["A"],
        "note": "12/3-4 = 0，在布尔上下文里是 FALSE；NULL AND FALSE = FALSE（AND 只要有一边假就是假）；"
                "NOT FALSE = TRUE。",
    },

    # ---------------- 二、数据库基本概念（DDL / DML / DCL、键、约束） ----------------
    {
        "key": "con_01",
        "kind": "choice",
        "title": "哪些语句属于 DDL",
        "level": "easy",
        "source": "L2 · SQL Part 1",
        "brief": "DDL 负责定义数据结构与约束。选出所有属于 DDL 的语句。",
        "stem": "下列哪些语句属于 DDL？",
        "options": [
            "CREATE TABLE",
            "ALTER TABLE",
            "DROP TABLE",
            "INSERT INTO",
            "GRANT SELECT",
        ],
        "answer": ["A", "B", "C"],
        "note": "DDL = 建/改/删结构（CREATE / ALTER / DROP）。INSERT 属于 DML，GRANT 属于 DCL。",
    },
    {
        "key": "con_02",
        "kind": "choice",
        "title": "哪些语句属于 DML",
        "level": "easy",
        "source": "L2 · SQL Part 1",
        "brief": "DML 负责对表里的数据增删改查。",
        "stem": "下列哪些语句属于 DML？",
        "options": ["SELECT", "INSERT", "UPDATE", "DELETE", "COMMIT"],
        "answer": ["A", "B", "C", "D"],
        "note": "SQL 的 DML 包含查询与增删改四类。COMMIT 属于事务控制，不在这三类里。",
    },
    {
        "key": "con_03",
        "kind": "choice",
        "title": "DCL 管什么",
        "level": "medium",
        "source": "L2 · SQL Part 1",
        "brief": "DCL = Data Control Language。选出所有正确说法。",
        "stem": "关于 DCL，下列哪些说法正确？",
        "options": [
            "负责用户权限与访问控制",
            "负责定义表结构",
            "GRANT 与 REVOKE 属于 DCL",
            "负责插入和删除数据",
            "负责给列选数据类型",
        ],
        "answer": ["A", "C"],
        "note": "DCL 只管「谁能做什么」：GRANT 授权、REVOKE 收回。定义结构是 DDL，增删数据是 DML。",
    },
    {
        "key": "con_04",
        "kind": "choice",
        "title": "主键与唯一键",
        "level": "medium",
        "source": "L2 · SQL Part 1",
        "brief": "MySQL 默认行为。选出所有正确说法。",
        "stem": "关于 PRIMARY KEY 与 UNIQUE，下列哪些正确？",
        "options": [
            "一张表只能有一个 PRIMARY KEY",
            "PRIMARY KEY 列允许 NULL",
            "UNIQUE 列允许 NULL",
            "UNIQUE 可以约束多列组合",
            "PRIMARY KEY 可以由多列组成",
        ],
        "answer": ["A", "C", "D", "E"],
        "note": "主键非空且唯一，一表只能一个（但可以是多列组合的复合主键）；UNIQUE 允许 NULL，"
                "也可以跨多列组合约束。",
    },
    {
        "key": "con_05",
        "kind": "choice",
        "title": "外键约束的规则",
        "level": "hard",
        "source": "Lab3 · Foreign Key",
        "brief": "假设使用 MySQL 默认设置。选出所有正确说法。",
        "stem": "关于外键约束，下列哪些正确？",
        "options": [
            "引用表与被引用表涉及的列数必须相同",
            "被引用的列必须是主键或 UNIQUE",
            "引用表里的外键列必须自己是主键",
            "一张表可以引用它自己",
            "一张表可以有多个外键",
            "外键列可以为 NULL",
        ],
        "answer": ["A", "B", "D", "E", "F"],
        "note": "外键列只要求「值能对上被引用列」，并不要求它自己是主键 —— 那是把主键和外键搞混了。"
                "自引用（如员工表的 managerId 指向本表 staffNo）是合法且常见的。",
    },
    {
        "key": "con_06",
        "kind": "choice",
        "title": "哪些数据类型写法不合法",
        "level": "medium",
        "source": "L2 · SQL Part 1",
        "brief": "只看语法，不管业务含义。选出所有**不合法**的写法。",
        "stem": "下列哪些列类型写法在 MySQL 里是语法错误？",
        "options": ["DECIMAL(5,7)", "NUMERIC(7,6)", "DATE(5)", "VARCHAR", "CHAR(1)", "STRING"],
        "answer": ["A", "C", "D", "F"],
        "note": "DECIMAL(M,D) 要求 M ≥ D，所以 (5,7) 非法；DATE 不带长度参数；VARCHAR 必须给长度；"
                "STRING 不是 MySQL 类型（那是 C#/Java 的）。",
    },

    # ---------------- 三、SQL 填空（Lab3 / Lab4 / Lab5） ----------------
    {
        "key": "sql_01",
        "kind": "blank",
        "title": "查出全部教师姓名",
        "level": "easy",
        "source": "Lab4 · SELECT Part 1",
        "brief": "只要姓名这一列，别的列不要。",
        "parts": [{
            "label": "",
            "lines": ["SELECT ____", "FROM Teacher;"],
        }],
        "blanks": [{
            "accept": ["name"],
            "hint": "只要一列，把列名写在 SELECT 后面。",
            "why": "SELECT 后面直接跟列名 name —— 写 * 会把所有列都取回来，不符合题意。",
        }],
        "note": "SELECT 列名 FROM 表名 是最基本的投影；写 * 是选出全部列。",
    },
    {
        "key": "sql_02",
        "kind": "blank",
        "title": "没选 MC1 的学生（子查询）",
        "level": "medium",
        "source": "Lab4 · SELECT Part 1",
        "brief": "题目要求用子查询。注意「没选」= 不在选了 MC1 的那批人里面。",
        "parts": [{
            "label": "",
            "lines": [
                "SELECT name FROM Student",
                "WHERE id ____ (SELECT id FROM Enrolment WHERE code = 'MC1');",
            ],
        }],
        "blanks": [{
            "accept": ["NOT IN"],
            "hint": "先求出选了 MC1 的 id 集合，再取「不在其中」。",
            "why": "用 NOT IN。写成 NOT EXISTS 需要改写子查询结构；只写 IN 会得到「选了 MC1 的人」，正好相反。",
        }],
        "note": "NOT IN 是「不在这个集合里」；集合里若有 NULL，NOT IN 会整体返回空结果 —— 这是它的经典坑。",
    },
    {
        "key": "sql_03",
        "kind": "blank",
        "title": "邮箱不以 @gmail.com 结尾",
        "level": "easy",
        "source": "Lab4 · SELECT Part 1",
        "brief": "用 NOT LIKE，写出匹配模式。",
        "parts": [{
            "label": "",
            "lines": ["SELECT name, email FROM Student", "WHERE email NOT LIKE '____';"],
        }],
        "blanks": [{
            "accept": ["%@gmail.com"],
            "hint": "% 匹配任意长度字符。要匹配「以 @gmail.com 结尾」，通配符放在哪边？",
            "why": "'%@gmail.com'：% 在前面表示前面任意内容，后面必须正好以 @gmail.com 收尾。"
                   "写成 '%gmail.com' 也常被判对，但不严谨（会命中 xxgmail.com）。",
        }],
        "note": "LIKE 里 % 匹配任意个字符、_ 匹配恰好一个字符。NOT LIKE 是取反。",
    },
    {
        "key": "sql_04",
        "kind": "blank",
        "title": "姓名里包含 ia",
        "level": "easy",
        "source": "Lab4 · SELECT Part 1",
        "brief": "「包含」= 前后都可能有别的字符。",
        "parts": [{
            "label": "",
            "lines": ["SELECT id, name FROM Student", "WHERE name LIKE '____';"],
        }],
        "blanks": [{
            "accept": ["%ia%"],
            "hint": "要匹配「中间含有 ia」，两边都要能容纳任意字符。",
            "why": "'%ia%'。只写 'ia%' 是以 ia 开头，'%ia' 是以 ia 结尾，都不等价于「包含」。",
        }],
        "note": "LIKE 默认不区分大小写（取决于列的 collation），这里按不区分处理。",
    },
    {
        "key": "sql_05",
        "kind": "blank",
        "title": "按价格从高到低排",
        "level": "easy",
        "source": "Lab5 · SELECT Part 2",
        "brief": "只要补排序方向关键字。",
        "parts": [{
            "label": "",
            "lines": ["SELECT title, price FROM CD", "ORDER BY price ____;"],
        }],
        "blanks": [{
            "accept": ["DESC"],
            "hint": "从高到低 = 降序。",
            "why": "用 DESC。不写默认是 ASC（升序），会得到从低到高。",
        }],
        "note": "ORDER BY 可以接多列：先按 genre 再按 price，写成 ORDER BY genre, price DESC。",
    },
    {
        "key": "sql_06",
        "kind": "blank",
        "title": "含税价（加 20%）并起别名",
        "level": "medium",
        "source": "Lab5 · SELECT Part 2",
        "brief": "库里的价格不含税，要乘上含税系数；列别名已经写好了。",
        "parts": [{
            "label": "",
            "lines": ["SELECT title, price * ____ AS `Full Price`", "FROM CD;"],
        }],
        "blanks": [{
            "accept": ["1.2"],
            "hint": "加 20% 相当于乘以多少？",
            "why": "填 1.2。写成 price * 1.2；写 1.20 也等价，但 0.2 是「只算税额」，不是含税价。",
        }],
        "note": "算术表达式要放在 SELECT 列表里；AS 后面用反引号包住带空格的别名。",
    },
    {
        "key": "sql_07",
        "kind": "blank",
        "title": "最便宜的 CD（聚合 + 别名）",
        "level": "medium",
        "source": "Lab5 · SELECT Part 2",
        "brief": "求最小值用聚合函数。",
        "parts": [{
            "label": "",
            "lines": ["SELECT ____(price) AS `Cheapest CD`", "FROM CD;"],
        }],
        "blanks": [{
            "accept": ["MIN"],
            "hint": "最小值、最大值、总数分别是哪三个函数？",
            "why": "用 MIN。MAX 是最贵、AVG 是平均、SUM 是总和 —— 题目要的是最低价。",
        }],
        "note": "聚合函数会把多行压成一行；不加 GROUP BY 时，SELECT 里只能出现聚合结果。",
    },
    {
        "key": "sql_08",
        "kind": "blank",
        "title": "INNER JOIN 的连接条件",
        "level": "medium",
        "source": "Lab5 · Homework · Join",
        "brief": "两表用 INNER JOIN 连起来，还差连接条件的关键字。",
        "parts": [{
            "label": "",
            "lines": [
                "SELECT author_id, name",
                "FROM books INNER JOIN authors_of_books ____ (books.id = authors_of_books.book_id)",
                "WHERE published < '2000-01-01';",
            ],
        }],
        "blanks": [{
            "accept": ["ON"],
            "hint": "JOIN 之后接哪个关键字写条件？",
            "why": "用 ON。USING 只能用于同名列，这里两边的列名不同（id / book_id），不能用 USING。",
        }],
        "note": "INNER JOIN ... ON ... 只保留匹配上的行；要保留左表全部行得用 LEFT OUTER JOIN。",
    },
    {
        "key": "sql_09",
        "kind": "blank",
        "title": "保留左表全部行",
        "level": "medium",
        "source": "Lab5 · Homework · Outer Join",
        "brief": "即使右表没有匹配，左表的行也要留下。",
        "parts": [{
            "label": "",
            "lines": [
                "SELECT student.id, code",
                "FROM student ____ OUTER JOIN enrolment ON (student.id = enrolment.id)",
                "WHERE name NOT LIKE '_ar_';",
            ],
        }],
        "blanks": [{
            "accept": ["LEFT"],
            "hint": "student 在 FROM 后面，是要被全部保留下来的那张表。",
            "why": "用 LEFT。RIGHT 会保留 enrolment 的全部行，和题目要求相反。",
        }],
        "note": "LEFT OUTER JOIN 保留左表所有行，右表没匹配的补 NULL。",
    },
    {
        "key": "sql_10",
        "kind": "blank",
        "title": "删表再重建（Lab4 的脚本开头）",
        "level": "easy",
        "source": "Lab4 · Homework",
        "brief": "脚本第一行先把可能已存在的表删掉，避免重复建表报错。",
        "parts": [{
            "label": "",
            "lines": ["____ TABLE IF EXISTS books, authors_of_books;"],
        }],
        "blanks": [{
            "accept": ["DROP"],
            "hint": "删除整张表用哪个动词？",
            "why": "用 DROP。DELETE 只删数据、表结构还在，而且不能一次删多张表。",
        }],
        "note": "DROP TABLE 属于 DDL；DELETE FROM 属于 DML。两者都会「删东西」，但删的对象不同。",
    },
    {
        "key": "sql_11",
        "kind": "blank",
        "title": "ALTER 加外键：级联删除",
        "level": "hard",
        "source": "Lab3 · Foreign Key 选项",
        "brief": "删除分支时，该分支下的员工也要跟着删掉；主键改了则把员工的分支号置空。",
        "parts": [{
            "label": "",
            "lines": [
                "ALTER TABLE staff",
                "  ADD FOREIGN KEY (branchNo) REFERENCES branch(branchNo)",
                "  ON DELETE ____",
                "  ON UPDATE SET NULL;",
            ],
        }],
        "blanks": [{
            "accept": ["CASCADE"],
            "hint": "「跟着一起删」对应的选项名。",
            "why": "用 CASCADE。SET NULL 是「把外键列置空」，RESTRICT 是「不让删」—— 都不符合「一起删除」。",
        }],
        "note": "外键的参照动作：ON DELETE / ON UPDATE 各能配 CASCADE、SET NULL、RESTRICT、NO ACTION。",
    },
]

SQL_TASK_MAP = {t["key"]: t for t in SQL_TASKS}


def public_task(t: dict) -> dict:
    """给前端的版本：去掉答案。选择题不传 answer，填空题不传 accept。"""
    out = {
        "key": t["key"],
        "kind": t["kind"],
        "title": t["title"],
        "level": t["level"],
        "source": t["source"],
        "brief": t["brief"],
        "note": t.get("note", ""),
        "total": len(t.get("blanks", [])) if t["kind"] == "blank" else 1,
    }
    if t["kind"] == "choice":
        out["stem"] = t["stem"]
        out["options"] = t["options"]
        out["multi"] = len(t["answer"]) > 1
    else:
        out["parts"] = t["parts"]
        out["blanks"] = [{"hint": b.get("hint", ""), "why": b.get("why", "")} for b in t["blanks"]]
    return out


def answer_key(t: dict) -> dict:
    """提交后才返回的答案。"""
    if t["kind"] == "choice":
        return {"answer": t["answer"]}
    return {"accept": [b.get("accept", []) for b in t["blanks"]]}
