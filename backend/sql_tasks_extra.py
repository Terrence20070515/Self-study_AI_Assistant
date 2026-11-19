"""SOE101 SQL 训练题库 · 第二批（写语句填空，覆盖 lecture 全部语法）。

第一批（sql_tasks.py）是 47 道：三值逻辑、概念多选、算结果、以及 11 道入门填空。
这批补的是「lecture 讲到、但第一批还没考到」的语法，按课的顺序排：

  sel_*   检索与排序：DISTINCT / CONCAT / ORDER BY 多列 / LIMIT OFFSET / BETWEEN /
          <> / LIKE / 比较运算放在 SELECT 列表里 / 日期函数
  log_*   逻辑与 NULL：AND 与 OR 的优先级 / IS NULL / IS NOT NULL / 子查询里先排 NULL
  sub_*   子查询与集合：标量子查询 / IN / NOT IN / EXISTS / ANY / ALL / 派生表 /
          UNION / UNION ALL / 用子查询模拟 EXCEPT 与 INTERSECT
  join_*  连接：CROSS / INNER / LEFT OUTER / RIGHT OUTER / NATURAL / USING /
          三表连接 / FULL OUTER 的 MySQL 替代写法
  agg_*   聚合与分组：COUNT(*) / SUM / AVG+ROUND / MIN / GROUP BY / WHERE 与 GROUP BY
          的先后 / COUNT(DISTINCT) / HAVING 与 ORDER BY
  ddl_*   建表与改表：CREATE SCHEMA / IF NOT EXISTS / DECIMAL / DATETIME /
          AUTO_INCREMENT / DEFAULT / CHECK / 表级主键 / ON DELETE CASCADE /
          ON UPDATE SET NULL / ADD CONSTRAINT / CHANGE COLUMN / MODIFY COLUMN /
          DROP FOREIGN KEY / DROP PRIMARY KEY / DROP TABLE IF EXISTS / CREATE INDEX /
          ALTER ... AUTO_INCREMENT = n
  dml_*   增删改：INSERT ... VALUES 多行 / INSERT ... SELECT / DELETE FROM / TRUNCATE

**每条语句都在真实 MySQL 8.0.33（默认 sql_mode，含 ONLY_FULL_GROUP_BY）里跑过**，
不是照着记忆写的。口径以课件为准：课件说「MySQL 只支持 UNION」，
所以 INTERSECT / EXCEPT 出成「用子查询怎么模拟」，而不是让你写那两个关键字。
"""

BLANK = "____"


def _b(accept, hint, why):
    return {"accept": list(accept), "hint": hint, "why": why}


def _q(key, title, level, source, brief, lines, blanks, note):
    """一条写语句填空题：parts 只有一段，行按顺序拼成一条 SQL。"""
    return {
        "key": key,
        "kind": "blank",
        "title": title,
        "level": level,
        "source": source,
        "brief": brief,
        "parts": [{"label": "", "lines": list(lines)}],
        "blanks": list(blanks),
        "note": note,
    }


EXTRA_SQL_TASKS = [
    # ==================== 一、检索与排序（L4 select part 1 / L5 part 2） ====================
    _q("sel_01", "每种曲风只出现一次", "easy", "L5 · DISTINCT",
       "CD 表里同一曲风有很多张，结果里只想要每个曲风一行。",
       ["SELECT ____ genre", "FROM CD;"],
       [_b(["DISTINCT"], "去掉结果里的重复行。", "DISTINCT 去重；不写就是默认的 ALL（不去重）。")],
       "DISTINCT 作用于整个 SELECT 列表（多列时是「整行相同」才去掉），"
       "不是只作用于紧跟它的那一列。"),

    _q("sel_02", "把姓和名拼成一列", "easy", "L4 · 字符串函数",
       "staff 表里 fName / lName 是两列，想拼成「名 姓」一列。",
       ["SELECT ____(fName, ' ', lName) AS full_name", "FROM staff;"],
       [_b(["CONCAT"], "把多个字符串接起来的函数。",
           "CONCAT(a, b, c) 按顺序拼接；任一参数为 NULL 时整个结果是 NULL"
           "（要兜住得用 IFNULL/COALESCE 包一层）。")],
       "MySQL 里字符串拼接用 CONCAT，不是用 + （+ 在 MySQL 里会被当成加法）。"),

    _q("sel_03", "同一门课里分数从高到低", "easy", "L5 · ORDER BY",
       "先按课程代码升序，同一门课内部按分数降序。",
       ["SELECT * FROM Grades", "ORDER BY Code ASC, Mark ____;"],
       [_b(["DESC"], "降序是哪个词？",
           "ORDER BY 可以给每一列单独指定方向：Code ASC, Mark DESC。不写方向默认 ASC。")],
       "ASC = 升序（默认），DESC = 降序。多列排序时前一个列相同时才看后一个。"),

    _q("sel_04", "跳过前三条，再取两条", "medium", "L5 · LIMIT",
       "按价格从高到低排完，要第 4、5 条（不要前三条）。",
       ["SELECT title, price FROM CD", "ORDER BY price DESC", "LIMIT 2 ____ 3;"],
       [_b(["OFFSET"], "跳过多少行用哪个词？",
           "LIMIT 行数 OFFSET 跳过行数。也可以写成 LIMIT 3, 2（先偏移、后行数），"
           "两种写法顺序正好相反，别记反。")],
       "LIMIT 不带 ORDER BY 时「第几条」是没有意义的 —— 数据库不保证顺序。"),

    _q("sel_05", "价格落在区间内", "easy", "L4 · BETWEEN",
       "把 9.99 到 12.99 之间的 CD 列出来。",
       ["SELECT title, price FROM CD", "WHERE price ____ 9.99 AND 12.99;"],
       [_b(["BETWEEN"], "「在两者之间」的关键字。",
           "BETWEEN a AND b 是闭区间，等价于 price >= 9.99 AND price <= 12.99，两端都包含。")],
       "BETWEEN 也可以用在日期上：WHERE d BETWEEN '2024-09-01' AND '2024-09-30'。"
       "注意 NOT BETWEEN 是取反。"),

    _q("sel_06", "排除某个曲风", "easy", "L4 · 比较运算符",
       "只要不是 Rock 的。",
       ["SELECT title FROM CD", "WHERE genre ____ 'Rock';"],
       [_b(["<>", "!="], "「不等于」怎么写？两种都合法。",
           "标准 SQL 是 <>，MySQL 也接受 !=。注意 NULL 用 <> 比较结果仍是 NULL，"
           "不会进结果 —— 排除空值要用 IS NOT NULL。")],
       "= 和 <> 遇到 NULL 都返回 NULL（不是 TRUE/FALSE），所以 NULL 只能靠 IS / IS NOT 判断。"),

    _q("sel_07", "名字里带 ia 的学生", "easy", "Lab4 · LIKE",
       "Lab4 原题：找出名字里包含 ia 的学生。",
       ["SELECT ID, Name FROM Student", "WHERE Name ____ '%ia%';"],
       [_b(["LIKE"], "模糊匹配用哪个关键字？",
           "LIKE 配 %（任意多个字符，含 0 个）和 _（恰好一个字符）。= 不支持通配符。")],
       "%ia% 表示「ia 出现在任意位置」；'ia%' 是以 ia 开头，'%ia' 是以 ia 结尾。"),

    _q("sel_08", "把比较结果当成一列", "medium", "L4 · 逻辑表达式",
       "每一行多出一列：分数够 40 就是 1，不够就是 0。",
       ["SELECT Name, Mark, Mark ____ 40 AS passed", "FROM Grades;"],
       [_b([">="], "「大于等于」怎么写？",
           "SQL 的比较表达式本身就是值（TRUE=1 / FALSE=0 / NULL），可以直接放进 SELECT 列表。")],
       "这是 L4 讲的「返回布尔值的语句也能放在 SELECT 段」。同样的写法还有 "
       "SELECT postcode LIKE 'gb%' FROM places。"),

    _q("sel_09", "按年份筛入职记录", "medium", "L4 · 日期函数",
       "只取今年入职的员工。",
       ["SELECT staffNo, recruit_date FROM staff", "WHERE ____(recruit_date) = YEAR(CURDATE());"],
       [_b(["YEAR"], "从日期里取出年份的函数名。",
           "YEAR(d) 取年份；配套还有 MONTH()、DAYOFMONTH()、DATE()（只取日期部分）。"
           "CURDATE() 是今天。")],
       "别写成 recruit_date LIKE '2024%' 去筛「今年」—— 年份一变就得改语句，用 YEAR() 才是通用的。"),

    # ==================== 二、逻辑与 NULL（L6 Missing Information） ====================
    _q("log_01", "括号决定 AND / OR 的范围", "medium", "L4 · 逻辑运算符",
       "要「Rock 和 Pop 两种曲风里，价格低于 12.99 的」。",
       ["SELECT title, price FROM CD",
        "WHERE (genre = 'Rock' OR genre = 'Pop')",
        "  ____ price < 12.99;"],
       [_b(["AND"], "两个条件都要满足。",
           "AND 的优先级高于 OR。不写括号会变成 genre='Rock' OR (genre='Pop' AND price<12.99)，"
           "Rock 那边完全不看价格。")],
       "只要混用 AND 和 OR，就加括号 —— 这既是正确性问题，也是给人看的问题。"),

    _q("log_02", "电话为空的员工", "easy", "L6 · IS NULL",
       "phone 列没填的员工。",
       ["SELECT staffNo, fName FROM staff", "WHERE phone ____ NULL;"],
       [_b(["IS"], "和 NULL 比较只能用哪个词？",
           "phone = NULL 的结果是 NULL（不是 TRUE），永远筛不出行；必须写 IS NULL。")],
       "NULL 不是「一个值」，所以不能用 = / <> 比较。这是 L6 整节课的核心。"),

    _q("log_03", "电话不为空的员工", "easy", "L6 · IS NOT NULL",
       "反过来：phone 有填的。",
       ["SELECT staffNo FROM staff", "WHERE phone IS ____ NULL;"],
       [_b(["NOT"], "取反。",
           "IS NOT NULL 判断「有值」。写成 phone <> NULL 一样是错的（结果恒为 NULL）。")],
       "统计「有电话的人数」时 COUNT(phone) 会自动跳过 NULL，不需要先 IS NOT NULL。"),

    _q("log_04", "NOT IN 之前先把 NULL 排掉", "hard", "L6 · NULL 与集合",
       "s2.c 里有 NULL，直接 NOT IN 会一行都筛不出来。在子查询里先过滤。",
       ["SELECT c FROM t", "WHERE c NOT IN (SELECT c FROM s2 ____ c IS NOT NULL);"],
       [_b(["WHERE"], "子查询里加条件用哪个词？",
           "c NOT IN (3, NULL) 展开成 c<>3 AND c<>NULL，后半段恒为 NULL，"
           "整个条件对任何行都不成立 —— 结果 0 行。先把 NULL 排除才有意义。")],
       "另一种更稳的写法是 NOT EXISTS：它判断「子查询有没有行」，不受 NULL 影响。"),

    # ==================== 三、子查询与集合（L5 part2 / L6） ====================
    _q("sub_01", "最贵的那张 CD", "easy", "L5 · 标量子查询",
       "子查询返回一个值，外层拿它做比较。",
       ["SELECT title, price FROM CD", "WHERE price = (SELECT ____(price) FROM CD);"],
       [_b(["MAX"], "取最大值的聚合函数。",
           "子查询只返回一个值（标量）时可以直接用 = 比较；返回一列多行就必须用 IN / ANY / ALL。")],
       "如果最贵的有多张，这条会全部返回 —— 这正是想要的。"),

    _q("sub_02", "选了 MC2 的学生", "easy", "Lab4 · IN 子查询",
       "Lab4 原题：retrieve the student IDs who study MC2。",
       ["SELECT ID, Name FROM Student",
        "WHERE ID ____ (SELECT ID FROM Enrolment WHERE Code = 'MC2');"],
       [_b(["IN"], "一个值要跟「一组值」比，用哪个？",
           "子查询返回一列多行，必须用 IN（或 = ANY），不能用 =，否则报 "
           "Subquery returns more than 1 row。")],
       "IN 后面也可以直接跟列表：WHERE Code IN ('MC1','MC2')，不必非得是子查询。"),

    _q("sub_03", "没选 MC1 的学生", "medium", "Lab4 · NOT IN 子查询",
       "Lab4 原题：names of students who do not take MC1（要求用子查询）。",
       ["SELECT Name FROM Student",
        "WHERE ID ____ IN (SELECT ID FROM Enrolment WHERE Code = 'MC1');"],
       [_b(["NOT"], "取反。",
           "NOT IN 的子查询如果可能返回 NULL，整个条件会失效 —— 这里是 ID 列（NOT NULL），安全。")],
       "Lab4 还有一题是「MC1、MC2、HCI-101 三个都不选」，写法是 NOT IN ('MC1','MC2','HCI-101')。"),

    _q("sub_04", "自己也是主管的员工", "medium", "L5 · EXISTS",
       "L5 原题：retrieve all info for employees who are also managers。",
       ["SELECT * FROM Employee AS E1",
        "WHERE ____ (SELECT * FROM Employee AS E2",
        "             WHERE E1.Name = E2.Manager);"],
       [_b(["EXISTS"], "判断「子查询有没有行」用哪个？",
           "EXISTS 只关心子查询有没有结果，不关心选出什么列 —— 所以写 SELECT * 或 SELECT 1 都一样。")],
       "EXISTS 是相关子查询：里面的 E1 来自外层，外层每换一行就要重算一次。"),

    _q("sub_05", "比 Andy 的某一次成绩高", "hard", "L5 · ANY",
       "Andy 有多次成绩，只要比他**任意一次**高就算。",
       ["SELECT Name, Mark FROM Grades",
        "WHERE Mark > ____ (SELECT Mark FROM Grades WHERE Name = 'Andy');"],
       [_b(["ANY"], "「存在一个满足」对应哪个关键字？",
           "> ANY 等价于 > MIN(...)：比集合里最小的那个大，就至少比一个成员大。"
           "写成 SOME 也对，是同义词。")],
       "> ANY 和 > ALL 差很多：> ALL 要求比**每一个**都大（即 > MAX）。"),

    _q("sub_06", "比 Andy 每一次成绩都高", "hard", "L5 · ALL",
       "这次要求比 Andy 的**所有**成绩都高。",
       ["SELECT Name, Mark FROM Grades",
        "WHERE Mark >= ____ (SELECT Mark FROM Grades WHERE Name = 'Andy');"],
       [_b(["ALL"], "「全部满足」对应哪个关键字？",
           ">= ALL 等价于 >= MAX(...)。集合为空时 ALL 恒为真（这点常被忽略）。")],
       "ANY = 至少一个，ALL = 全部；NOT IN 其实等价于 <> ALL。"),

    _q("sub_07", "FROM 里的子查询必须起别名", "medium", "L5 · 派生表",
       "把子查询当成一张临时表来查。",
       ["SELECT * FROM (SELECT name, email FROM teachers) ____ t",
        "WHERE t.email IS NOT NULL;"],
       [_b(["AS"], "给这张临时表一个名字。",
           "FROM 里的子查询没有表名，MySQL 会报 Every derived table must have its own alias。"
           "AS 可以省略，但别名必须有。")],
       "派生表（derived table）就是「先查出一张临时表，再在外面查它」，"
       "常用于先聚合再筛选。"),

    _q("sub_08", "每个人的平均分加上总平均", "medium", "L6 · UNION",
       "一行一个人的平均分，最后再加一行 Total。",
       ["SELECT Name, AVG(Mark) AS Average FROM Grades GROUP BY Name", "____",
        "SELECT 'Total' AS Name, AVG(Mark) AS Average FROM Grades;"],
       [_b(["UNION"], "把两个结果上下拼起来。",
           "UNION 要求两边列数相同、类型相容（union compatible），列名取第一个 SELECT 的。")],
       "UNION 会去重（内部要排序），知道不会重复时用 UNION ALL 更快。"),

    _q("sub_09", "两张表直接拼起来、不去重", "easy", "L6 · UNION ALL",
       "r 和 s 结构相同，要 8 行全要。",
       ["SELECT * FROM r", "UNION ____", "SELECT * FROM s;"],
       [_b(["ALL"], "不去重的话加哪个词？",
           "UNION ALL 直接拼接；UNION 会去重。这两张表本来没有完全相同的行，"
           "所以两者行数相同 —— 但那是数据巧合，不是规则。")],
       "UNION 的去重是有代价的（要排序/建临时表）；确定不会重复就别用。"),

    _q("sub_10", "用子查询模拟 EXCEPT", "hard", "L6 · 集合差",
       "课件口径：MySQL 只支持 UNION，A EXCEPT B 要自己写。",
       ["SELECT c FROM r", "WHERE c ____ IN (SELECT c FROM s WHERE c IS NOT NULL);"],
       [_b(["NOT"], "「在 A 里、不在 B 里」= 对 B 取反。",
           "A EXCEPT B = A 里那些不在 B 里的行。写成 NOT IN 时，B 里若有 NULL 会整段失效，"
           "所以子查询里先加 c IS NOT NULL。")],
       "更稳的写法是 NOT EXISTS：WHERE NOT EXISTS (SELECT 1 FROM s WHERE s.c = r.c)。"),

    _q("sub_11", "用两个 IN 模拟 INTERSECT", "hard", "L6 · 集合交",
       "同时出现在 s 和 s2 里的 c。",
       ["SELECT DISTINCT c FROM r", "WHERE c IN (SELECT c FROM s)", "  ____ c IN (SELECT c FROM s2);"],
       [_b(["AND"], "两个条件同时满足。",
           "交集 = 属于 A 且属于 B，两个 IN 用 AND 连。写成 UNION 会得到并集，正好相反。")],
       "这条只从 r 里挑，所以结果是「r ∩ s ∩ s2」。要纯 s ∩ s2 就把外层换成 s。"),

    # ==================== 四、连接（L5 · Joins） ====================
    _q("join_01", "两张表的所有组合", "easy", "L5 · CROSS JOIN",
       "学生 × 选课，不做任何匹配。",
       ["SELECT * FROM Student", "____ JOIN Enrolment;"],
       [_b(["CROSS"], "笛卡尔积对应哪种 JOIN？",
           "CROSS JOIN 就是笛卡尔积（等价于 FROM Student, Enrolment），行数 = 两表行数相乘。")],
       "L5 也讲了：CROSS JOIN + WHERE 等价于 INNER JOIN，只是写法不同。"),

    _q("join_02", "只保留匹配上的行", "easy", "L5 · INNER JOIN",
       "学生和他的选课，没选课的不要。",
       ["SELECT s.Name, e.Code", "FROM Student s", "____ JOIN Enrolment e ON s.ID = e.ID;"],
       [_b(["INNER"], "只返回匹配成功的行，是哪种 JOIN？",
           "INNER JOIN 只保留 ON 条件成立的行；JOIN 单独写默认就是 INNER。")],
       "INNER JOIN 可以用 WHERE 代替（FROM a, b WHERE a.id=b.id），结果一样，"
       "但 JOIN ... ON 把「连接条件」和「筛选条件」分开了，更好读。"),

    _q("join_03", "没选课的学生也要出现", "medium", "L5 · LEFT OUTER JOIN",
       "以左表（Student）为准，右表匹配不上就补 NULL。",
       ["SELECT s.Name, e.Code", "FROM Student s", "____ OUTER JOIN Enrolment e ON s.ID = e.ID;"],
       [_b(["LEFT"], "以左边的表为准是哪个方向？",
           "LEFT OUTER JOIN 保留左表全部行，右表没有匹配的列补 NULL。")],
       "OUTER 可以省略：LEFT JOIN 就等于 LEFT OUTER JOIN。"),

    _q("join_04", "以选课表为准", "medium", "L5 · RIGHT OUTER JOIN",
       "反过来：以右表（Enrolment）为准。",
       ["SELECT s.Name, e.Code", "FROM Student s", "____ OUTER JOIN Enrolment e ON s.ID = e.ID;"],
       [_b(["RIGHT"], "以右边的表为准是哪个方向？",
           "RIGHT OUTER JOIN 保留右表全部行。它等价于把两张表位置对调写 LEFT JOIN。")],
       "实际项目里几乎只用 LEFT JOIN —— 换个表顺序就能表达同样的意思，"
       "混用两种方向容易把自己绕进去。"),

    _q("join_05", "同名自动连接", "medium", "L5 · NATURAL JOIN",
       "两张表有同名列 ID，不写 ON。",
       ["SELECT * FROM Student", "____ JOIN Enrolment;"],
       [_b(["NATURAL"], "按所有同名列自动连接是哪种 JOIN？",
           "NATURAL JOIN = INNER JOIN + 自动把**所有**同名列当连接条件 + 结果里同名列只留一份。")],
       "NATURAL JOIN 的风险：两张表除了 ID 还有别的同名列（比如都叫 Name）时，"
       "条件会变成 AND 上去，结果莫名其妙变少。"),

    _q("join_06", "用 USING 指定同名列", "medium", "L5 · USING",
       "只想按 ID 连接，但不要 NATURAL 的「自动全同名列」。",
       ["SELECT s.Name, e.Code", "FROM Student s JOIN Enrolment e", "____ (ID);"],
       [_b(["USING"], "指定「按哪一列连」的子句。",
           "USING(ID) 等价于 ON s.ID = e.ID，并且结果里 ID 只出现一次（和 NATURAL JOIN 一样）。")],
       "ON 更通用（可以写不等式、可以连不同名的列）；USING 只在两边列名相同时才用得上。"),

    _q("join_07", "三张表连起来", "medium", "Lab5 · 多表连接",
       "学生 → 成绩 → 课程，要学生名、课程名、分数。",
       ["SELECT s.Name, m.Title, g.Mark", "FROM Student s",
        "JOIN Grade g ____ s.ID = g.ID", "JOIN Module m ON m.Code = g.Code;"],
       [_b(["ON"], "连接条件用哪个词引出？",
           "每个 JOIN 后面跟 ON <条件>。三个表以上就一条 JOIN 接一条，从近到远连过去。")],
       "连接 N 张表至少需要 N-1 个连接条件；少写一个就变成笛卡尔积（行数爆炸）。"),

    _q("join_08", "MySQL 没有 FULL OUTER JOIN", "hard", "L5 · FULL OUTER",
       "两边都要保留。MySQL 不支持 FULL OUTER JOIN，要用左右连接拼。",
       ["SELECT * FROM Student LEFT OUTER JOIN Enrolment ON Student.ID = Enrolment.ID", "____",
        "SELECT * FROM Student RIGHT OUTER JOIN Enrolment ON Student.ID = Enrolment.ID;"],
       [_b(["UNION"], "把两个结果合起来、并去重。",
           "LEFT 的结果 + RIGHT 的结果，用 UNION（不是 UNION ALL）拼起来，"
           "中间重复的那部分正好被去掉 —— 就是 FULL OUTER JOIN。")],
       "课件原话：Only Left and Right outer joins are supported in MySQL。"
       "写 FULL OUTER JOIN 在 MySQL 里直接语法错误。"),

    # ==================== 五、聚合与分组（L5 · Aggregate / GROUP BY） ====================
    _q("agg_01", "一共有多少张 CD", "easy", "L5 · COUNT",
       "数行数。",
       ["SELECT ____(*) AS n FROM CD;"],
       [_b(["COUNT"], "数行数用哪个聚合函数？",
           "COUNT(*) 数行数（含全 NULL 的行）；COUNT(列) 只数该列非 NULL 的行。")],
       "COUNT(*) 和 COUNT(1) 在 MySQL 里性能一样；别用 COUNT(列) 去数行数，"
       "那一列有 NULL 就会少数。"),

    _q("agg_02", "所有 CD 的价格总和", "easy", "L5 · SUM",
       "求和。",
       ["SELECT ____(price) AS total FROM CD;"],
       [_b(["SUM"], "求和用哪个？",
           "SUM 只对数值列有效；有 NULL 的行会被跳过（不是当 0，但结果相当于忽略）。")],
       "SUM 作用在空集上返回 NULL，不是 0 —— 要 0 得写 IFNULL(SUM(x), 0)。"),

    _q("agg_03", "平均价格保留两位", "easy", "L5 · AVG + ROUND",
       "平均值，四舍五入到两位小数。",
       ["SELECT ROUND(____(price), 2) AS avg_price FROM CD;"],
       [_b(["AVG"], "求平均用哪个？",
           "AVG 会跳过 NULL 行；ROUND(x, 2) 保留两位小数。两者可以嵌套。")],
       "AVG(price) 的分母是「price 非 NULL 的行数」，不是总行数 —— 这点和直觉不同。"),

    _q("agg_04", "最贵和最便宜差多少", "medium", "L5 · MIN / MAX",
       "Lab5 原题：difference between the most expensive and cheapest CD。",
       ["SELECT MAX(price) - ____(price) AS `CD Price Range`", "FROM CD;"],
       [_b(["MIN"], "求最小用哪个？",
           "MAX - MIN 就是极差。别名带空格必须用反引号包起来。")],
       "聚合函数不能直接嵌套（MAX(MIN(x)) 是错的），但可以相减、相加。"),

    _q("agg_05", "按曲风分组计数", "easy", "L5 · GROUP BY",
       "每种曲风各有多少张。",
       ["SELECT genre, COUNT(*) AS n", "FROM CD", "____ genre;"],
       [_b(["GROUP BY"], "分组用哪两个词？",
           "GROUP BY 列：把该列值相同的行归成一组，每组输出一行。")],
       "SELECT 里只能出现「分组列」和「聚合函数」—— 这是 ONLY_FULL_GROUP_BY "
       "（MySQL 8 默认开启）强制要求的，写别的列会直接报错。"),

    _q("agg_06", "先筛行，再分组", "medium", "L5 · WHERE 与 GROUP BY 的顺序",
       "只统计价格大于 5 的 CD。",
       ["SELECT genre, AVG(price) AS avg_price", "FROM CD", "____ price > 5", "GROUP BY genre;"],
       [_b(["WHERE"], "筛「行」用哪个？筛「组」又用哪个？",
           "WHERE 在 GROUP BY 之前筛行；HAVING 在之后筛组。顺序写反会直接语法错误。")],
       "执行顺序：FROM → WHERE → GROUP BY → 聚合 → HAVING → SELECT → ORDER BY → LIMIT。"),

    _q("agg_07", "有多少种不同的价格", "medium", "L5 · COUNT DISTINCT",
       "Lab5 原题：number of different prices。",
       ["SELECT COUNT(____ price) AS n", "FROM CD;"],
       [_b(["DISTINCT"], "先去重再计数。",
           "COUNT(DISTINCT price) 数「不同的非 NULL 值」有几个；"
           "COUNT(price) 数「非 NULL 的行」有几行。")],
       "DISTINCT 放在聚合函数括号里面：COUNT(DISTINCT col)，不是 COUNT(col) DISTINCT。"),

    _q("agg_08", "分组后再筛、再排序", "medium", "L5 · HAVING + ORDER BY",
       "曲风数量超过 2 的，按数量从多到少。",
       ["SELECT genre, COUNT(*) AS n", "FROM CD", "GROUP BY genre",
        "____ COUNT(*) > 2", "ORDER BY n DESC;"],
       [_b(["HAVING"], "分组后筛「组」用哪个？",
           "HAVING 里可以用聚合函数，WHERE 里不行 —— 因为 WHERE 执行时还没算聚合。")],
       "HAVING 里写 COUNT(*) 很常见；MySQL 也允许 HAVING n > 2 直接用别名，"
       "但标准 SQL 不支持，考试写 COUNT(*) 更稳。"),

    # ==================== 六、建表与改表（L2 / L3） ====================
    _q("ddl_01", "新建一个 schema", "easy", "Lab2 · CREATE SCHEMA",
       "Lab2 第一步：建一个自己的库。",
       ["CREATE ____ cpt103_lab2;"],
       [_b(["SCHEMA", "DATABASE"], "MySQL 里「库」用哪个词？两个都行。",
           "CREATE SCHEMA 和 CREATE DATABASE 在 MySQL 里是同义词。"
           "建完要 USE cpt103_lab2 才能在里面建表，否则报 no database selected。")],
       "课件里的 schema ≈ 其他数据库里的 database。MySQL 不强制「schema 里再分 schema」。"),

    _q("ddl_02", "重复建表不报错", "medium", "L2 · IF NOT EXISTS",
       "脚本反复跑，表已经存在时不要报错。",
       ["CREATE TABLE ____ books (", "  book_id INT PRIMARY KEY,", "  name VARCHAR(20)", ");"],
       [_b(["IF NOT EXISTS"], "「不存在才建」怎么写？",
           "CREATE TABLE IF NOT EXISTS ... 表存在时只给 warning，不报错。")],
       "配套的是 DROP TABLE IF EXISTS —— 脚本开头先删再建，就能反复跑。"),

    _q("ddl_03", "价格该用什么类型", "easy", "L2 · DECIMAL",
       "金额精确到分，总共不超过 5 位数字。",
       ["CREATE TABLE CD (", "  cd_id INT PRIMARY KEY,", "  price ____(5,2)", ");"],
       [_b(["DECIMAL", "NUMERIC"], "定点小数用哪个类型？",
           "DECIMAL(5,2) = 总共 5 位、其中 2 位小数，范围到 999.99。"
           "金额别用 FLOAT —— 二进制浮点存不下 0.1，算钱会差几分。")],
       "DECIMAL 和 NUMERIC 在 MySQL 里是同一个东西。"),

    _q("ddl_04", "登录时间要精确到秒", "easy", "L2 · DATETIME",
       "time1 是 TIMESTAMP，time2 要存「年月日时分秒」。",
       ["CREATE TABLE `ts_test` (", "  `time1` TIMESTAMP,", "  `time2` ____", ");"],
       [_b(["DATETIME"], "不带时区转换的日期时间类型。",
           "DATETIME 原样存；TIMESTAMP 存 UTC、取出来按会话时区转换，范围只到 2038 年。")],
       "只存日期用 DATE，存到秒用 DATETIME，需要时区自动换算才用 TIMESTAMP。"),

    _q("ddl_05", "让 id 自动编号", "medium", "L2 · AUTO_INCREMENT",
       "插入时不指定 id，让 MySQL 自己加 1。",
       ["CREATE TABLE Persons (", "  Id INT ____ PRIMARY KEY,", "  lastname VARCHAR(255) NOT NULL", ");"],
       [_b(["AUTO_INCREMENT"], "自动递增的属性名。",
           "AUTO_INCREMENT 必须用在键列上（主键或唯一键）。插入时给 NULL 或省略该列就会自动取值。")],
       "删掉的行号不会复用；也可以手动指定值覆盖它。起始值用 "
       "ALTER TABLE Persons AUTO_INCREMENT = 100 改。"),

    _q("ddl_06", "给年龄一个默认值", "easy", "L2 · DEFAULT",
       "插入时不给 age，就按 12 算。",
       ["CREATE TABLE Persons (", "  lastname VARCHAR(255) NOT NULL,", "  age INT ____ 12", ");"],
       [_b(["DEFAULT"], "默认值用哪个词？",
           "DEFAULT 值：插入时省略该列就用它。DEFAULT NULL 表示默认是 NULL（可空列的隐式默认）。")],
       "不写 DEFAULT 时 MySQL 会按类型给隐式默认：可空列默认 NULL，NOT NULL 列没有默认值，"
       "插入时必须给。"),

    _q("ddl_07", "限制 id 必须为正", "medium", "L2 · CHECK",
       "用命名约束限制取值范围。",
       ["CREATE TABLE People (", "  id INTEGER PRIMARY KEY,", "  name VARCHAR(100) NOT NULL,",
        "  CONSTRAINT id_positive ____ (id > 0)", ");"],
       [_b(["CHECK"], "取值范围约束叫什么？",
           "CHECK (条件)：不满足就插入/更新失败。MySQL 8.0.16 起才真正生效，"
           "更早的版本会静默忽略。")],
       "课件特别标注了 8.0.16+ —— 在老版本上写了 CHECK 等于没写，这也是考试爱考的点。"),

    _q("ddl_08", "表级主键约束", "medium", "L2 · 表级约束",
       "把主键写成独立的约束，并起个名字。",
       ["CREATE TABLE Branch (", "  branchNo CHAR(4),", "  city VARCHAR(25),",
        "  CONSTRAINT branchPK ____ KEY (branchNo)", ");"],
       [_b(["PRIMARY"], "主键的完整叫法。",
           "表级写法 PRIMARY KEY (col) 可以跨多列（复合主键）；列级写法只能写在列后面。")],
       "命名约束（CONSTRAINT 名字 ...）的好处是以后能按名字删："
       "ALTER TABLE Branch DROP PRIMARY KEY。"),

    _q("ddl_09", "删分店时员工一起删", "medium", "Lab3 · ON DELETE CASCADE",
       "Lab3 Task 2：分支被删，该分支的员工也跟着删。",
       ["ALTER TABLE staff", "ADD CONSTRAINT fk_staff_branch FOREIGN KEY (branchNo)",
        "  REFERENCES branch(branchNo)", "  ON DELETE ____;"],
       [_b(["CASCADE"], "「跟着一起删」用哪个参照动作？",
           "ON DELETE CASCADE：父行删掉，子行一起删。"
           "另有 SET NULL（置空）、RESTRICT / NO ACTION（不让删，默认）。")],
       "默认是 RESTRICT —— 有子行引用时直接拒绝删除。Lab3 Task 3 让你删 B001 就是为了看这个。"),

    _q("ddl_10", "分店改号时员工置空", "medium", "Lab3 · ON UPDATE SET NULL",
       "Lab3 Task 2 的另一半：branchNo 被改，员工的 branchNo 置为 NULL。",
       ["ALTER TABLE staff", "ADD CONSTRAINT fk_staff_branch FOREIGN KEY (branchNo)",
        "  REFERENCES branch(branchNo)", "  ON DELETE CASCADE", "  ON UPDATE ____ NULL;"],
       [_b(["SET"], "「置为 NULL」是两个词，第一个是什么？",
           "ON UPDATE SET NULL：父键改了，子表对应列置 NULL（该列必须允许 NULL）。")],
       "ON DELETE 和 ON UPDATE 可以配不同的动作，Lab3 要求的正是 "
       "ON DELETE CASCADE + ON UPDATE SET NULL。"),

    _q("ddl_11", "给已有表加约束", "easy", "L2 · ALTER ADD CONSTRAINT",
       "表已经建好了，再补一个唯一约束。",
       ["ALTER TABLE branch", "____ CONSTRAINT ck_branch UNIQUE (street);"],
       [_b(["ADD"], "加东西用哪个动词？",
           "ALTER TABLE ... ADD CONSTRAINT 名字 约束类型 (列)。也可以 ADD COLUMN 加列。")],
       "ALTER TABLE 一次可以干很多事，但每条语句只写一件事最不容易出错。"),

    _q("ddl_12", "改列名 + 改类型", "medium", "L2 · CHANGE COLUMN",
       "把 fName 改名成 first_name，同时把长度改成 20。",
       ["ALTER TABLE staff", "____ COLUMN fName first_name VARCHAR(20) NOT NULL;"],
       [_b(["CHANGE"], "既改名又改类型用哪个？",
           "CHANGE COLUMN 旧名 新名 类型：必须写两遍列名。只改类型用 MODIFY。")],
       "CHANGE 必须把新类型重新写一遍 —— 不写就是语法错误，不会「保持原类型」。"),

    _q("ddl_13", "只改类型、不改名", "easy", "L2 · MODIFY COLUMN",
       "first_name 还是叫 first_name，只把长度从 20 加到 40。",
       ["ALTER TABLE staff", "____ COLUMN first_name VARCHAR(40) NOT NULL;"],
       [_b(["MODIFY"], "只改定义用哪个？",
           "MODIFY COLUMN 列名 新类型：列名只写一次。改名要用 CHANGE。")],
       "记法：CHANGE 要「旧名 + 新名」（两个名字），MODIFY 只有一个名字。"),

    _q("ddl_14", "删掉外键约束", "medium", "L2 · DROP FOREIGN KEY",
       "外键挡住了删表，先把它删掉。",
       ["ALTER TABLE staff", "DROP ____ fk_staff_branch;"],
       [_b(["FOREIGN KEY"], "删外键要用哪两个词？",
           "DROP FOREIGN KEY 名字。注意删外键用的是**约束名**，不是列名。")],
       "四种删法别混：DROP INDEX 删唯一键、DROP FOREIGN KEY 删外键、"
       "DROP PRIMARY KEY 删主键、DROP CHECK 删检查约束。"),

    _q("ddl_15", "删掉主键", "medium", "L2 · DROP PRIMARY KEY",
       "把 staff 的主键去掉。",
       ["ALTER TABLE staff", "DROP ____ KEY;"],
       [_b(["PRIMARY"], "主键是哪种 KEY？",
           "DROP PRIMARY KEY 后面不跟名字 —— 一张表只有一个主键。")],
       "删主键前要确认没有外键指着它，否则会报错。"),

    _q("ddl_16", "删表时别报错", "easy", "L5 · DROP TABLE IF EXISTS",
       "Lab5 的建表脚本第一行：先删掉可能存在的两张表。",
       ["DROP TABLE ____ books, authors_of_books;"],
       [_b(["IF EXISTS"], "「存在才删」怎么写？",
           "DROP TABLE IF EXISTS a, b; 一条语句可以删多张表，用逗号分隔。")],
       "删多张有外键关系的表要注意顺序：先删引用方（子表），再删被引用方（父表）。"),

    _q("ddl_17", "给连接列建索引", "medium", "L2 · CREATE INDEX",
       "staff.branchNo 经常用来连接，加个索引。",
       ["CREATE ____ idx_staff_branch ON staff (branchNo);"],
       [_b(["INDEX"], "建索引用哪个词？（UNIQUE 是另一回事）",
           "CREATE INDEX 名字 ON 表 (列)。加 UNIQUE 就是唯一索引。")],
       "主键和外键在 MySQL 里会自动建索引；普通查询列才需要手动加。"),

    _q("ddl_18", "改自增起始值", "medium", "L2 · AUTO_INCREMENT 起始值",
       "让下一条自动编号从 100 开始。",
       ["ALTER TABLE Persons", "____ = 100;"],
       [_b(["AUTO_INCREMENT"], "要改的那个属性名。",
           "ALTER TABLE 表名 AUTO_INCREMENT = n：只影响之后插入的值，已有行不动。")],
       "也可以在 CREATE TABLE 末尾直接写 ) AUTO_INCREMENT = 5;。"),

    # ==================== 七、增删改（L2 · DML） ====================
    _q("dml_01", "一次插两行", "easy", "L2 · INSERT 多行",
       "一条 INSERT 插两条记录。",
       ["INSERT INTO my_table", "____ (1, 'ABC'), (2, 'def');"],
       [_b(["VALUES"], "插入值用哪个词？",
           "INSERT INTO 表 VALUES (...), (...)：多个括号用逗号分隔就是多行。")],
       "值的顺序必须和表的列顺序一致；不确定就显式写列名："
       "INSERT INTO my_table (column1, column2) VALUES ...。"),

    _q("dml_02", "把查询结果插进另一张表", "medium", "L2 · INSERT ... SELECT",
       "把 student 的 id、name 复制到 archive。",
       ["INSERT INTO archive (id, name)", "____ id, name FROM Student;"],
       [_b(["SELECT"], "插入的来源是一段查询，用哪个关键字开头？",
           "INSERT INTO 表 (列...) SELECT ...：不需要 VALUES，直接把查询结果插进去。")],
       "INSERT ... SELECT 常用于备份、归档、把中间结果落表；列数和类型要对得上。"),

    _q("dml_03", "清空表但保留结构", "easy", "L2 · TRUNCATE",
       "把 staff 的数据全清掉，表本身还要留着。",
       ["TRUNCATE ____ staff;"],
       [_b(["TABLE"], "TRUNCATE 后面跟哪个词？",
           "TRUNCATE TABLE 表名：清空所有行，比 DELETE FROM 快（不逐行记日志），"
           "但不能带 WHERE、也不能回滚。")],
       "TRUNCATE 属于 DDL（隐式提交），DELETE 属于 DML（可回滚）。"),

    _q("dml_04", "删掉一整张表的数据", "easy", "Lab3 · DELETE",
       "不用 WHERE，把 staff 全部清空（结构保留、可回滚）。",
       ["DELETE ____ staff;"],
       [_b(["FROM"], "DELETE 后面跟表名，中间差一个介词。",
           "DELETE FROM 表 是 DML，可以回滚；DROP TABLE 连表结构一起删，是 DDL。")],
       "不带 WHERE 的 DELETE 会把整张表清空 —— 执行前先 SELECT COUNT(*) 看一眼。"),
]
