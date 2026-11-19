"""SQL 训练的「表结构」参考。

学生要写 `WHERE phone IS NULL`，得先知道 staff 有没有 phone 列、叫什么。
只给一句题干就等于让人瞎猜列名 —— 所以每道写语句题都挂一张表结构卡。

命名口径按课件与 lab：Student(ID, Name, Email)、Enrolment(ID, Code)、
Module(Code, Title, Credits, Teacher)、CD(cd_id, title, price, genre, artist_id)…
MySQL 的列名不分大小写，学生写 `student.id` 和 `Student.ID` 都能跑。

这份数据同时被 `scripts/verify_sql_mysql.py` 拿来核对 —— 它会拿这里的
表名/列名去比对 information_schema，只要有一处和真实库对不上就报错。
这样「卡片上写的」和「数据库里有的」不可能漂移。
"""


def _c(name, type_, key=""):
    return {"name": name, "type": type_, "key": key}


SCHEMA = {
    "branch": [
        _c("branchNo", "CHAR(4)", "PK"),
        _c("street", "VARCHAR(100)"),
        _c("city", "VARCHAR(25)"),
        _c("postcode", "VARCHAR(10)"),
    ],
    "staff": [
        _c("staffNo", "CHAR(4)", "PK"),
        _c("fName", "VARCHAR(20)"),
        _c("lName", "VARCHAR(20)"),
        _c("branchNo", "CHAR(4)", "FK → branch"),
        _c("salary", "DECIMAL(8,2)"),
        _c("phone", "VARCHAR(20)"),
        _c("recruit_date", "DATE"),
    ],
    "CD": [
        _c("cd_id", "INT", "PK"),
        _c("title", "VARCHAR(60)"),
        _c("price", "DECIMAL(5,2)"),
        _c("genre", "VARCHAR(20)"),
        _c("artist_id", "INT", "FK → Artist"),
    ],
    "Artist": [
        _c("artist_id", "INT", "PK"),
        _c("name", "VARCHAR(40)"),
    ],
    "Student": [
        _c("ID", "INT", "PK"),
        _c("Name", "VARCHAR(40)"),
        _c("Email", "VARCHAR(60)"),
        _c("Phone", "VARCHAR(20)"),
    ],
    "Enrolment": [
        _c("ID", "INT", "PK"),
        _c("Code", "VARCHAR(10)", "PK"),
    ],
    "Module": [
        _c("Code", "VARCHAR(10)", "PK"),
        _c("Title", "VARCHAR(60)"),
        _c("Credits", "INT"),
        _c("Teacher", "VARCHAR(40)"),
    ],
    "Grade": [
        _c("ID", "INT"),
        _c("Code", "VARCHAR(10)"),
        _c("Mark", "INT"),
        _c("YearTaken", "INT"),
    ],
    "Grades": [
        _c("Name", "VARCHAR(20)"),
        _c("Code", "VARCHAR(10)"),
        _c("Mark", "INT"),
    ],
    "teachers": [
        _c("name", "VARCHAR(40)"),
        _c("email", "VARCHAR(60)"),
        _c("office", "VARCHAR(20)"),
        _c("telephone", "VARCHAR(20)"),
    ],
    "Teacher": [
        _c("name", "VARCHAR(40)"),
        _c("email", "VARCHAR(60)"),
    ],
    "books": [
        _c("book_id", "INT", "PK"),
        _c("name", "VARCHAR(40)"),
        _c("published", "DATE"),
    ],
    "authors_of_books": [
        _c("author_id", "INT", "PK"),
        _c("book_id", "INT", "PK"),
    ],
    "Employee": [
        _c("Name", "VARCHAR(20)"),
        _c("Dept", "VARCHAR(20)"),
        _c("Manager", "VARCHAR(20)"),
        _c("Salary", "INT"),
        _c("Phone", "VARCHAR(20)"),
    ],
    "r": [_c("a", "INT"), _c("b", "INT"), _c("c", "INT")],
    "s": [_c("a", "INT"), _c("b", "INT"), _c("c", "INT")],
    "t": [_c("a", "INT"), _c("b", "INT"), _c("c", "INT")],
    "s2": [_c("c", "INT")],
    "my_table": [_c("column1", "INT"), _c("column2", "VARCHAR(40)")],
    "archive": [_c("id", "INT"), _c("name", "VARCHAR(40)")],
}

# 每道写语句题要用到哪些表。建表类的题（学生自己定义列）不挂表结构。
SQL_REFS = {
    # ---- 第一批 ----
    "sql_01": ["Teacher"],
    "sql_02": ["Student", "Enrolment"],
    "sql_03": ["Student"],
    "sql_04": ["Student"],
    "sql_05": ["CD"],
    "sql_06": ["CD"],
    "sql_07": ["CD"],
    "sql_08": ["books", "authors_of_books"],
    "sql_09": ["Student", "Enrolment"],
    "sql_10": ["books", "authors_of_books"],
    "sql_11": ["staff", "branch"],
    "w_02": ["branch"],
    "w_03": ["CD"],
    "w_04": ["Enrolment"],
    "w_05": ["staff"],
    "w_08": ["Student", "Enrolment"],
    "w_09": ["CD"],
    "w_10": ["CD"],
    "w_11": ["CD"],
    # ---- 检索与排序 ----
    "sel_01": ["CD"],
    "sel_02": ["staff"],
    "sel_03": ["Grades"],
    "sel_04": ["CD"],
    "sel_05": ["CD"],
    "sel_06": ["CD"],
    "sel_07": ["Student"],
    "sel_08": ["Grades"],
    "sel_09": ["staff"],
    # ---- 逻辑与 NULL ----
    "log_01": ["CD"],
    "log_02": ["staff"],
    "log_03": ["staff"],
    "log_04": ["t", "s2"],
    # ---- 子查询与集合 ----
    "sub_01": ["CD"],
    "sub_02": ["Student", "Enrolment"],
    "sub_03": ["Student", "Enrolment"],
    "sub_04": ["Employee"],
    "sub_05": ["Grades"],
    "sub_06": ["Grades"],
    "sub_07": ["teachers"],
    "sub_08": ["Grades"],
    "sub_09": ["r", "s"],
    "sub_10": ["r", "s"],
    "sub_11": ["r", "s", "s2"],
    # ---- 连接 ----
    "join_01": ["Student", "Enrolment"],
    "join_02": ["Student", "Enrolment"],
    "join_03": ["Student", "Enrolment"],
    "join_04": ["Student", "Enrolment"],
    "join_05": ["Student", "Enrolment"],
    "join_06": ["Student", "Enrolment"],
    "join_07": ["Student", "Grade", "Module"],
    "join_08": ["Student", "Enrolment"],
    # ---- 聚合与分组 ----
    "agg_01": ["CD"],
    "agg_02": ["CD"],
    "agg_03": ["CD"],
    "agg_04": ["CD"],
    "agg_05": ["CD"],
    "agg_06": ["CD"],
    "agg_07": ["CD"],
    "agg_08": ["CD"],
    # ---- 建表改表（只列「改已有表」的，建表题不列） ----
    "ddl_09": ["staff", "branch"],
    "ddl_10": ["staff", "branch"],
    "ddl_11": ["branch"],
    "ddl_12": ["staff"],
    "ddl_13": ["staff"],
    "ddl_14": ["staff"],
    "ddl_15": ["staff"],
    "ddl_16": ["books", "authors_of_books"],
    "ddl_17": ["staff"],
    # ---- 增删改 ----
    "dml_01": ["my_table"],
    "dml_02": ["archive", "Student"],
    "dml_03": ["staff"],
    "dml_04": ["staff"],
}


def schema_for(key: str) -> list:
    """按题号取表结构；没配就返回空列表（前端不渲染这张卡）。"""
    return [
        {"name": t, "columns": SCHEMA[t]}
        for t in SQL_REFS.get(key, [])
        if t in SCHEMA
    ]
