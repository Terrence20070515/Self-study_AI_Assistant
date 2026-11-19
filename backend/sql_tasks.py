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

    # ---------------- 四、给表算结果（画表 + 查询 → 判断结果） ----------------
    # 表数据取自课程那份 CPT103 SQL Revision（R / S 两张关系），答案逐条用 sqlite 跑过
    {
        "key": "tbl_01",
        "kind": "table",
        "title": "UNION 去重后哪些元组不在结果里",
        "level": "medium",
        "source": "Revision · 集合运算",
        "brief": "r 和 s 结构相同。UNION 会去重，先想清楚两表合起来一共剩几行。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select distinct * from (select * from r union select * from s) as t;",
        "question": "下列哪个元组**没有**出现在结果里？",
        "options": ["(2, 1, 3)", "(3, 3, 1)", "(3, 3, 4)", "(1, 1, 3)"],
        "answer": ["A"],
        "note": "两表各 4 行且没有完全相同的行，UNION 后是 8 行。除了 (2,1,3)，另外三个都在里面。"
                "注意 UNION 去重、UNION ALL 不去重，这题若换成 UNION ALL 就是 8 行不变、但不会多也不会少。",
    },
    {
        "key": "tbl_02",
        "kind": "table",
        "title": "IN 子查询：哪一行被筛掉",
        "level": "medium",
        "source": "Revision · 子查询",
        "brief": "子查询取的是 s 的 b 列，不是 s 的 a 列 —— 这是最容易看错的地方。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select * from r where a in (select distinct b from s);",
        "question": "下列哪一行**不在**结果里？",
        "options": ["(1, 2, 3)", "(2, 3, 6)", "(4, 1, 3)", "(3, 3, 1)"],
        "answer": ["C"],
        "note": "s.b 的去重集合是 {2, 3, 1}，所以 r 里 a 为 1、2、3 的行都留下；"
                "(4,1,3) 的 a=4 不在集合里，被筛掉。",
    },
    {
        "key": "tbl_03",
        "kind": "table",
        "title": "换一组数据再做一次 IN 子查询",
        "level": "medium",
        "source": "Revision · 子查询",
        "brief": "表换了一份，但查询一模一样。别凭上一题的记忆答。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[7, 1, 5], [5, 2, 1], [4, 6, 1], [7, 3, 1]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[3, 5, 1], [6, 3, 6], [8, 7, 3], [4, 2, 3]]},
        ],
        "query": "select * from r where a in (select distinct b from s);",
        "question": "下列哪一行**不在**结果里？",
        "options": ["(7, 1, 5)", "(5, 2, 1)", "(7, 3, 1)", "(4, 6, 1)"],
        "answer": ["D"],
        "note": "s.b = {5, 3, 7, 2}，r 里 a 为 7、5、7 的三行留下（7 出现两次都留），a=4 的 (4,6,1) 被筛掉。",
    },
    {
        "key": "tbl_04",
        "kind": "table",
        "title": "笛卡尔积 + 条件：结果几行",
        "level": "medium",
        "source": "Revision · 连接",
        "brief": "FROM r, s 不带条件就是 4×4=16 行，再按 where 过滤。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select count(*) from r, s where r.a > s.a;",
        "question": "这条查询返回的数字是多少？",
        "options": ["3", "4", "5", "6"],
        "answer": ["B"],
        "note": "16 个组合里逐个比：r.a=1 时没有 s.a 更小；r.a=2 时 s.a=1 命中 1 个；"
                "r.a=3 时 s.a=1 命中 1 个；r.a=4 时 s.a=1、3 命中 2 个。合计 4。",
    },
    {
        "key": "tbl_05",
        "kind": "table",
        "title": "UNION 里两个 SELECT 列数不同吗",
        "level": "hard",
        "source": "Revision · 集合运算",
        "brief": "左边取 a、b，右边取 b、c。列数相同但含义不同 —— 想清楚每一列来自哪。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select * from (select distinct a, b from r union select b, c from s) as t;",
        "question": "关于这个结果，下列哪些说法正确？",
        "options": [
            "结果一共 6 行",
            "(3, 3) 在结果里",
            "(2, 2) 在结果里",
            "结果第二列的和等于 16",
        ],
        "answer": ["A", "B", "D"],
        "note": "左边 (1,2)(2,3)(3,3)(4,1)；右边 s 的 (b,c) 是 (2,3)(3,4)(1,3)(1,3)，去重后三个。"
                "合起来并去重：(1,2)(1,3)(2,3)(3,3)(3,4)(4,1) 共 6 行，第二列 2+3+3+3+4+1=16。"
                "(2,2) 不在其中。",
    },
    {
        "key": "tbl_06",
        "kind": "table",
        "title": "NOT IN 遇上 NULL 子查询",
        "level": "hard",
        "source": "Revision · 三值逻辑",
        "brief": "t 的 c 列有 NULL，子查询结果里也有 NULL。先别急着数行，想想 NOT IN 怎么展开。",
        "tables": [
            {"name": "t", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, None], [3, 3, 1]]},
            {"name": "s2", "columns": ["c"], "rows": [[3], [None]]},
        ],
        "query": "select * from t where c not in (select c from s2);",
        "question": "这条查询返回几行？",
        "options": ["0 行", "1 行", "2 行", "3 行"],
        "answer": ["A"],
        "note": "c NOT IN (3, NULL) 等价于 c<>3 AND c<>NULL。后面那半永远是 NULL，"
                "所以整个条件对任何行都不成立 —— 结果 0 行。（换成 IN 会返回 1 行：(1,2,3)。）"
                "这也是为什么子查询里要先排除 NULL。",
    },
    {
        "key": "tbl_07",
        "kind": "table",
        "title": "左连接会补出几行空",
        "level": "medium",
        "source": "Lab5 · Outer Join",
        "brief": "student 左连接 enrolment：没选课的学生也要出现。",
        "tables": [
            {"name": "student", "columns": ["id", "name"],
             "rows": [[1, "Ann"], [2, "Bob"], [3, "Cara"]]},
            {"name": "enrolment", "columns": ["id", "code"],
             "rows": [[1, "MC1"], [1, "MC2"]]},
        ],
        "query": "select s.id, s.name, e.code\nfrom student s left join enrolment e on s.id = e.id;",
        "question": "结果里 code 为 NULL 的行有几行？",
        "options": ["0 行", "1 行", "2 行", "3 行"],
        "answer": ["C"],
        "note": "Ann 有两条选课记录，出两行；Bob 和 Cara 在 enrolment 里没有匹配，"
                "左连接补 NULL 各出一行 —— 一共 4 行，其中 2 行 code 为 NULL。",
    },

    # ---------------- 五、给表算结果（填空版：同 Revision 的 Q17-3「返回 ___ 行」） ----------------
    {
        "key": "tblb_01",
        "kind": "table_blank",
        "title": "natural join 后还剩几行",
        "level": "hard",
        "source": "Revision · Q17-3",
        "brief": "t1 把 r 的 a 列改名成 b，再用 natural join 和 s 的子查询按 b 连。注意 where 条件用的是哪个 b、哪个 c。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[7, 1, 5], [5, 2, 1], [4, 6, 1], [7, 3, 1]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[3, 5, 1], [6, 3, 6], [8, 7, 3], [4, 2, 3]]},
        ],
        "query": "select * from (select a b, c from r) as t1\nnatural join (select a, b from s) as t2\nwhere b > c;",
        "question": "这条查询会返回 ____ 行（只填数字）",
        "blanks": [{
            "accept": ["3", "3 行", "3行"],
            "hint": "先看 t1 有哪两列、t2 有哪两列，natural join 是按同名的那一列连的。",
            "why": "t1=(b,c) 共 4 行，t2=(a,b) 共 4 行，按 b 连接后只剩 b 匹配上的组合；"
                   "再要求 b > c，符合的只有 3 行。",
        }],
        "note": "natural join 自动按「所有同名列」连，不写 ON；t1 用 `select a b` 把 a 改名成 b，"
                "就是为了让它和 t2 的 b 对上 —— 这是这类题的核心机关。",
    },
    {
        "key": "tblb_02",
        "kind": "table_blank",
        "title": "笛卡尔积里满足条件的组合数",
        "level": "medium",
        "source": "Revision · 连接",
        "brief": "FROM r, s 是 4×4=16 种组合，数一数其中有多少满足条件。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select count(*) from r, s where r.a > s.a;",
        "question": "这条查询返回的数字是 ____",
        "blanks": [{
            "accept": ["4"],
            "hint": "按 r 的每一行分别数：这一行的 a 比 s 里几个 a 大？",
            "why": "r.a=1 时 0 个；r.a=2 时 s.a=1 一个；r.a=3 时 s.a=1 一个；r.a=4 时 s.a=1、3 两个。合计 4。",
        }],
        "note": "count(*) 数的是结果行数，不是某个列的值。",
    },
    {
        "key": "tblb_03",
        "kind": "table_blank",
        "title": "去重后还剩几个不同的值",
        "level": "easy",
        "source": "Revision · 投影",
        "brief": "distinct 只作用在被选出的那一列上。",
        "tables": [
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select distinct b from s;",
        "question": "结果有 ____ 行（只填数字）",
        "blanks": [{
            "accept": ["3", "3 行", "3行"],
            "hint": "把 s 的 b 列抄下来：2、3、1、1 —— 有几个不同的值？",
            "why": "b 列是 2、3、1、1，去重后是 2、3、1 三个值。",
        }],
        "note": "distinct 去的是「整行重复」，这里是单列所以等于去重该列的重复值。"
                "注意 count(*) 会是 3、count(b) 会是 4 —— 区别在于有没有去重。",
    },
    {
        "key": "tblb_04",
        "kind": "table_blank",
        "title": "UNION ALL 到底几行",
        "level": "medium",
        "source": "Revision · 集合运算",
        "brief": "把 union 换成 union all，再用 count(*) 数。",
        "tables": [
            {"name": "r", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, 6], [3, 3, 1], [4, 1, 3]]},
            {"name": "s", "columns": ["a", "b", "c"],
             "rows": [[4, 2, 3], [3, 3, 4], [1, 1, 3], [8, 1, 3]]},
        ],
        "query": "select count(*) from (select * from r union all select * from s) as t;",
        "question": "返回的数字是 ____",
        "blanks": [{
            "accept": ["8"],
            "hint": "union all 去不去重？先回答这句，再数行。",
            "why": "union all 不去重，两张 4 行的表直接拼起来就是 8 行。若写成 union 也是 8 行"
                   "（这两张表本来没有完全相同的行）—— 但那是巧合，不是规则。",
        }],
        "note": "union = 合并后去重；union all = 直接拼、不去重。数据里有重复时两者行数才会不同。",
    },
    {
        "key": "tblb_05",
        "kind": "table_blank",
        "title": "左连接之后一共几行",
        "level": "medium",
        "source": "Lab5 · Outer Join",
        "brief": "先数右表里每个人有几条记录，再看左表里谁没有。",
        "tables": [
            {"name": "student", "columns": ["id", "name"],
             "rows": [[1, "Ann"], [2, "Bob"], [3, "Cara"]]},
            {"name": "enrolment", "columns": ["id", "code"],
             "rows": [[1, "MC1"], [1, "MC2"]]},
        ],
        "query": "select count(*) from student s\nleft join enrolment e on s.id = e.id;",
        "question": "结果有 ____ 行（只填数字）",
        "blanks": [{
            "accept": ["4", "4 行", "4行"],
            "hint": "左连接不是「每个学生一行」—— 有两条选课记录的学生会出现两次。",
            "why": "Ann 匹配到 2 条 → 2 行；Bob、Cara 没匹配但因为是左连接，各补一行 NULL → 2 行。合计 4。",
        }],
        "note": "左连接的行数 = 匹配上的组合数 + 左表里没匹配上的行数。不是左表的行数。",
    },
    {
        "key": "tblb_06",
        "kind": "table_blank",
        "title": "NOT IN 遇到 NULL 还剩几行",
        "level": "hard",
        "source": "Revision · 三值逻辑",
        "brief": "子查询结果里有 NULL。别急着数，先把 NOT IN 展开成比较式。",
        "tables": [
            {"name": "t", "columns": ["a", "b", "c"],
             "rows": [[1, 2, 3], [2, 3, None], [3, 3, 1]]},
            {"name": "s2", "columns": ["c"], "rows": [[3], [None]]},
        ],
        "query": "select count(*) from t where c not in (select c from s2);",
        "question": "返回的数字是 ____",
        "blanks": [{
            "accept": ["0", "0 行", "0行"],
            "hint": "c NOT IN (3, NULL) 展开成什么？其中一半是否恒为 NULL？",
            "why": "展开成 c<>3 AND c<>NULL。c<>NULL 永远是 NULL，AND 一边 NULL 一边假也是假/未知，"
                   "所以没有任何行满足 —— 返回 0。",
        }],
        "note": "这是 NOT IN 最著名的坑。要「不在集合里」且子查询可能有 NULL 时，"
                "要么先 where c is not null，要么改用 NOT EXISTS。",
    },

    # ---------------- 六、写语句填空（DDL / DML / 约束 / 子查询） ----------------
    {
        "key": "w_01",
        "kind": "blank",
        "title": "建表：两列该用什么类型",
        "level": "easy",
        "source": "Lab4 · Homework Task 3",
        "brief": "books 表：id 是整数，published 是出版日期。按 Lab4 给的脚本口径填。",
        "parts": [{
            "label": "",
            "lines": [
                "CREATE TABLE books (",
                "  id ____,",
                "  name VARCHAR(20),",
                "  published ____",
                ");",
            ],
        }],
        "blanks": [
            {"accept": ["INT", "INTEGER"], "hint": "整数用哪个类型？",
             "why": "id 是整数，写 INT（INTEGER 同义）。"},
            {"accept": ["DATE"], "hint": "只存年月日、不带时间，用哪个类型？",
             "why": "published 只到「日」，用 DATE；要精确到时分秒才用 DATETIME。"},
        ],
        "note": "建表时类型选错不会立刻报错，但之后插入或比较会出问题。"
                "INT / VARCHAR(n) / DATE 是最常用的三个。",
    },
    {
        "key": "w_02",
        "kind": "blank",
        "title": "插入一行数据",
        "level": "easy",
        "source": "Lab3 · Task 1",
        "brief": "给 branch 表插一条记录。",
        "parts": [{
            "label": "",
            "lines": ["INSERT ____ branch VALUES ('B005', 'p5');"],
        }],
        "blanks": [{
            "accept": ["INTO"],
            "hint": "INSERT 后面必须跟哪个介词？",
            "why": "INSERT INTO 表名 VALUES (...)。漏掉 INTO 直接语法错误。",
        }],
        "note": "插入属于 DML；列的顺序要和表定义一致，或者显式写 INSERT INTO branch(branchNo, postcode)。",
    },
    {
        "key": "w_03",
        "kind": "blank",
        "title": "改数据：把某类 CD 涨价",
        "level": "easy",
        "source": "Lab5 · SELECT Part 2",
        "brief": "把 Rock 类别的价格上调 20%。",
        "parts": [{
            "label": "",
            "lines": ["UPDATE CD", "____ price = price * 1.2", "WHERE genre = 'Rock';"],
        }],
        "blanks": [{
            "accept": ["SET"],
            "hint": "UPDATE 表名之后、赋值之前，用哪个关键字？",
            "why": "UPDATE … SET 列 = 值 WHERE …。漏掉 SET 是最常见的语法错误。",
        }],
        "note": "WHERE 千万别漏 —— 不写 WHERE 会把整张表都改掉。",
    },
    {
        "key": "w_04",
        "kind": "blank",
        "title": "删数据：只删一条",
        "level": "easy",
        "source": "Lab3 · Task 3",
        "brief": "删掉学号为 156123 的选课记录（表结构还在）。",
        "parts": [{
            "label": "",
            "lines": ["DELETE ____ enrolment", "WHERE id = 156123;"],
        }],
        "blanks": [{
            "accept": ["FROM"],
            "hint": "DELETE 后面要跟表名，中间差一个介词。",
            "why": "DELETE FROM 表名 WHERE …。这和 DROP TABLE（连表结构一起删）不是一回事。",
        }],
        "note": "DELETE FROM 只删行，属于 DML；DROP TABLE 删整张表，属于 DDL。",
    },
    {
        "key": "w_05",
        "kind": "blank",
        "title": "给已有表加一列",
        "level": "medium",
        "source": "L2 · ALTER TABLE",
        "brief": "staff 表要加一列 salary，类型 DECIMAL(8,2)。",
        "parts": [{
            "label": "",
            "lines": ["ALTER TABLE staff", "____ COLUMN salary DECIMAL(8,2);"],
        }],
        "blanks": [{
            "accept": ["ADD"],
            "hint": "「新增」这一列用哪个动词？（不是 MODIFY，那是改已有的列）",
            "why": "用 ADD COLUMN。MODIFY COLUMN 是修改已存在的列的属性，删列用 DROP COLUMN。",
        }],
        "note": "ALTER TABLE 的四件常用事：ADD / DROP / MODIFY（MySQL）/ CHANGE（改名+改类型）。",
    },
    {
        "key": "w_06",
        "kind": "blank",
        "title": "自引用外键：员工指向自己的上级",
        "level": "hard",
        "source": "Lab3 · Foreign Key",
        "brief": "managerNo 引用同一张表的 staffNo（主管也是员工）。",
        "parts": [{
            "label": "",
            "lines": [
                "CREATE TABLE staff (",
                "  staffNo CHAR(4) PRIMARY KEY,",
                "  managerNo CHAR(4),",
                "  FOREIGN KEY (managerNo) ____ staff(staffNo)",
                ");",
            ],
        }],
        "blanks": [{
            "accept": ["REFERENCES"],
            "hint": "外键要说明「引用哪张表的哪一列」，哪个关键字负责这件事？",
            "why": "写 REFERENCES staff(staffNo)。也可以写成 FOREIGN KEY … REFERENCES 的完整形式。",
        }],
        "note": "外键可以指向本表 —— 这就是「自引用」，组织架构、分类树都用它。",
    },
    {
        "key": "w_07",
        "kind": "blank",
        "title": "两列组合起来必须唯一",
        "level": "medium",
        "source": "L2 · 约束",
        "brief": "同一本书的同一个作者只能出现一次。",
        "parts": [{
            "label": "",
            "lines": [
                "CREATE TABLE authors_of_books (",
                "  author_id INT,",
                "  book_id INT,",
                "  ____ (author_id, book_id)",
                ");",
            ],
        }],
        "blanks": [{
            "accept": ["UNIQUE", "PRIMARY KEY"],
            "hint": "「组合起来不能重复」可以用哪个约束？两种写法都行，但语义不同。",
            "why": "UNIQUE (author_id, book_id) 最贴合题意（允许 NULL、可多个）；"
                   "写 PRIMARY KEY 也合法，但一张表只能有一个主键，语义变成「这张表靠这两列识别」。",
        }],
        "note": "UNIQUE 可以跨多列组合，且允许多个 NULL；主键不行。",
    },
    {
        "key": "w_08",
        "kind": "blank",
        "title": "子查询：没选 MC1 的学生",
        "level": "medium",
        "source": "Lab4 · SELECT Part 1",
        "brief": "用 EXISTS 的写法（不是 IN）。",
        "parts": [{
            "label": "",
            "lines": [
                "SELECT name FROM Student s",
                "WHERE ____ EXISTS (",
                "  SELECT 1 FROM Enrolment e",
                "  WHERE e.id = s.id AND e.code = 'MC1'",
                ");",
            ],
        }],
        "blanks": [{
            "accept": ["NOT"],
            "hint": "「没选」= 那个查询查不到任何行。",
            "why": "NOT EXISTS：子查询查不到行时才为真。写 EXISTS 会得到「选了 MC1 的人」，正好相反。",
        }],
        "note": "NOT EXISTS 比 NOT IN 安全：子查询里有 NULL 时 NOT IN 会整段失效，NOT EXISTS 不会。",
    },
    {
        "key": "w_09",
        "kind": "blank",
        "title": "分组之后再筛：哪种曲风超过 2 张",
        "level": "medium",
        "source": "Lab5 · SELECT Part 2",
        "brief": "WHERE 不能筛聚合结果，要用另一个关键字。",
        "parts": [{
            "label": "",
            "lines": [
                "SELECT genre, COUNT(*) AS n",
                "FROM CD",
                "GROUP BY genre",
                "____ COUNT(*) > 2;",
            ],
        }],
        "blanks": [{
            "accept": ["HAVING"],
            "hint": "WHERE 在分组前筛行；分组后筛「组」用哪个？",
            "why": "用 HAVING。写 WHERE 会报错或筛错 —— 聚合函数不能出现在 WHERE 里。",
        }],
        "note": "执行顺序：FROM → WHERE（筛行）→ GROUP BY → HAVING（筛组）→ ORDER BY → LIMIT。",
    },
    {
        "key": "w_10",
        "kind": "blank",
        "title": "只要最贵的那一张",
        "level": "medium",
        "source": "Lab5 · SELECT Part 2",
        "brief": "先按价格降序，再只取第一行。",
        "parts": [{
            "label": "",
            "lines": ["SELECT title, price FROM CD", "ORDER BY price DESC", "____ 1;"],
        }],
        "blanks": [{
            "accept": ["LIMIT", "LIMIT 1"],
            "hint": "MySQL 里「只取前 N 行」的关键字。",
            "why": "写 LIMIT 1（这里是只填空，所以填 LIMIT）。SQL Server 用 TOP、Oracle 用 ROWNUM，MySQL 用 LIMIT。",
        }],
        "note": "ORDER BY 是排序、LIMIT 是截断，两者经常一起用来取「最 X 的一条」。",
    },
    {
        "key": "w_11",
        "kind": "blank",
        "title": "给算出来的列起名字",
        "level": "easy",
        "source": "Lab5 · SELECT Part 2",
        "brief": "含税价那一列最后要叫 `Full Price`。",
        "parts": [{
            "label": "",
            "lines": ["SELECT title, ROUND(price * 1.2, 2) ____ `Full Price`", "FROM CD;"],
        }],
        "blanks": [{
            "accept": ["AS"],
            "hint": "给表达式/列起别名用哪个词？（也可以省略，但这里要填）",
            "why": "写 AS `Full Price`（反引号）。别名带空格时必须用反引号包起来，否则会被当成两个词。",
        }],
        "note": "AS 也可以省（SELECT price p），但加上更清楚；别名里带空格时反引号不能省。",
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
        "total": len(t.get("blanks", [])) if t["kind"] in ("blank", "table_blank") else 1,
    }
    if t["kind"] == "table_blank":
        out["tables"] = t["tables"]
        out["query"] = t["query"]
        out["question"] = t["question"]
        out["blanks"] = [{"hint": b.get("hint", ""), "why": b.get("why", "")} for b in t["blanks"]]
    elif t["kind"] in ("choice", "table"):
        if t["kind"] == "choice":
            out["stem"] = t["stem"]
        else:
            out["tables"] = t["tables"]
            out["query"] = t["query"]
            out["question"] = t["question"]
        out["options"] = t["options"]
        out["multi"] = len(t["answer"]) > 1
    else:
        out["parts"] = t["parts"]
        out["blanks"] = [{"hint": b.get("hint", ""), "why": b.get("why", "")} for b in t["blanks"]]
    return out


def answer_key(t: dict) -> dict:
    """提交后才返回的答案。"""
    if t["kind"] in ("choice", "table"):
        return {"answer": t["answer"]}
    return {"accept": [b.get("accept", []) for b in t["blanks"]]}
