"""把 SQL 题库存里的每条语句，放进真实 MySQL 里跑一遍。

为什么要有这个脚本：题库是手写的，SQL 对不对不能靠看。写法上差一个词
（`ON UPDATE SET NULL`、`CHANGE COLUMN` 要写两遍列名）在 SQLite / 记忆里
都不一定暴露，只有真数据库会报错。

做法：
  · 起一个干净的库 vt，灌一套和课程 lab 同名的表（branch/staff/CD/Student/...）
  · 每道题在**独立重建**的库里执行 —— DDL 会隐式提交，事务回滚救不了
  · 一道题有多个可接受答案时，逐个替换后各跑一次（每次只变一个空，其余取第一个）
  · SELECT 类记录行数，用来判断语句是不是「能跑但筛空了」

用法：python scripts/verify_sql_mysql.py
依赖：本机 mysqld 在 /tmp/mysql.sock（见 README 里的说明），pymysql
"""

import os
import re
import sys

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.sql_tasks import SQL_TASKS  # noqa: E402

SOCKET = os.environ.get("VERIFY_MYSQL_SOCKET", "/tmp/mysql.sock")
DB = "vt"
BLANK = "____"

SEED = r"""
CREATE TABLE branch (
  branchNo CHAR(4) NOT NULL PRIMARY KEY,
  street VARCHAR(100),
  city VARCHAR(25),
  postcode VARCHAR(10)
);
INSERT INTO branch VALUES
 ('B001','1 Main St','Liverpool','L1 1AA'),
 ('B002','2 Queen Rd','Liverpool','L1 2BB'),
 ('B003','3 Park Ave','Chester','CH1 3CC'),
 ('B004','4 King St','Chester','CH1 4DD');

CREATE TABLE staff (
  staffNo CHAR(4) PRIMARY KEY,
  fName VARCHAR(20),
  lName VARCHAR(20),
  branchNo CHAR(4),
  salary DECIMAL(8,2),
  phone VARCHAR(20) NULL,
  recruit_date DATE
);
INSERT INTO staff VALUES
 ('S001','Mary','Howe','B001',32000.00,'0151 111 1111','2026-01-15'),
 ('S002','John','Drake','B001',28000.00,NULL,'2023-01-15'),
 ('S003','Felicia','Gomez','B002',30000.00,'0151 222 2222','2026-02-10'),
 ('S004','Dave','Moe','B002',26000.50,NULL,'2022-11-20'),
 ('S005','Ann','Lee','B003',41000.00,'0151 333 3333','2026-03-05'),
 ('S006','Cara','Ng','B004',21000.00,'0151 444 4444','2021-06-30');

CREATE TABLE Artist (artist_id INT PRIMARY KEY, name VARCHAR(40));
INSERT INTO Artist VALUES (1,'Radiohead'),(2,'Daft Punk'),(3,'Miles Davis');

CREATE TABLE CD (
  cd_id INT PRIMARY KEY, title VARCHAR(60),
  price DECIMAL(5,2), genre VARCHAR(20), artist_id INT
);
INSERT INTO CD VALUES
 (1,'OK Computer',9.99,'Rock',1),
 (2,'Kid A',9.99,'Rock',1),
 (3,'Discovery',11.50,'Electronica',2),
 (4,'Homework',12.99,'Electronica',2),
 (5,'Kind of Blue',7.50,'Jazz',3),
 (6,'Amnesiac',10.00,'Rock',1),
 (7,'Random Access Memories',13.99,'Electronica',2),
 (8,'Bitches Brew',9.99,'Jazz',3);

CREATE TABLE Student (
  ID INT PRIMARY KEY, Name VARCHAR(40), Email VARCHAR(60), Phone VARCHAR(20)
);
INSERT INTO Student VALUES
 (156123,'Nuno Bloggs','nuno@bloggs.com',NULL),
 (156897,'John Trump','John@trump.com','123'),
 (123987,'Lidia Elliott','Lidia@gmail.com','456'),
 (777123,'Alicia Smith','Alicia123@456.com',NULL),
 (127845,'Sophie Johns','S.Johns@nott.edu.cn','789');

CREATE TABLE Enrolment (ID INT, Code VARCHAR(10), PRIMARY KEY (ID, Code));
INSERT INTO Enrolment VALUES
 (156123,'HSB'),(156123,'HCI-101'),
 (156897,'HSB'),(156897,'MC1'),(156897,'MC2'),
 (777123,'MC2'),
 (127845,'HSB'),(127845,'HCI-101'),(127845,'MC1'),(127845,'MC2');

CREATE TABLE Module (Code VARCHAR(10) PRIMARY KEY, Title VARCHAR(60), Credits INT, Teacher VARCHAR(40));
INSERT INTO Module VALUES
 ('MC1','Mathematics',10,'John Cartwright'),
 ('MC2','Advanced Mathematics',10,'Dave Moe'),
 ('HSB','Haskell for Beginners',5,'Felicia Gomez'),
 ('HCI-101','Human Computer Interaction',5,'John Drake');

CREATE TABLE Grade (ID INT, Code VARCHAR(10), Mark INT, YearTaken INT);
INSERT INTO Grade VALUES
 (156123,'HSB',65,1),(156897,'MC1',72,1),(156897,'MC2',58,1),
 (777123,'MC2',81,1),(127845,'MC1',44,1),(127845,'MC2',66,1);

CREATE TABLE Grades (Name VARCHAR(20), Code VARCHAR(10), Mark INT);
INSERT INTO Grades VALUES
 ('Andy','MC1',55),('Andy','MC2',72),
 ('Bea','MC1',40),('Bea','MC2',66),
 ('Cara','MC1',38),('Cara','MC2',81),
 ('Dan','MC1',66),('Dan','MC2',66),
 ('Eve','MC1',44),('Eve','MC2',90);

CREATE TABLE teachers (
  name VARCHAR(40), email VARCHAR(60), office VARCHAR(20), telephone VARCHAR(20)
);
INSERT INTO teachers VALUES
 ('John Drake','j.drake@xjtlu.edu.cn','SD-766','12022017202020'),
 ('Felicia Gomez','f.gomez@xjtlu.edu.cn','BES-207','1024'),
 ('John Cartwright','j.cartwright@xjtlu.edu.cn','BES-201','12345 ext 1212'),
 ('Dave Moe',NULL,'BES-205',NULL);

CREATE TABLE Teacher (name VARCHAR(40), email VARCHAR(60));
INSERT INTO Teacher VALUES ('John Drake','j.drake@xjtlu.edu.cn'),('Dave Moe','d.moe@xjtlu.edu.cn');

CREATE TABLE books (book_id INT PRIMARY KEY, name VARCHAR(40), published DATE);
INSERT INTO books VALUES
 (1,'Cryptonomicon','1999-01-01'),(2,'Applied Cryptography','1996-01-01'),
 (3,'Clouds','2010-05-05'),(4,'Cloud computing','2014-11-11');

CREATE TABLE authors_of_books (author_id INT, book_id INT, UNIQUE(author_id, book_id));
INSERT INTO authors_of_books VALUES (1,1),(2,2);

CREATE TABLE Employee (Name VARCHAR(20), Dept VARCHAR(20), Manager VARCHAR(20), Salary INT, Phone VARCHAR(20));
INSERT INTO Employee VALUES
 ('Boss','D1',NULL,20000,'111'),
 ('Andy','D1','Boss',12000,NULL),
 ('Cara','D2','Boss',15000,'222');

CREATE TABLE r (a INT, b INT, c INT);
INSERT INTO r VALUES (1,2,3),(2,3,6),(3,3,1),(4,1,3);

CREATE TABLE s (a INT, b INT, c INT);
INSERT INTO s VALUES (4,2,3),(3,3,4),(1,1,3),(8,1,3);

CREATE TABLE s2 (c INT);
INSERT INTO s2 VALUES (3),(NULL);

CREATE TABLE t (a INT, b INT, c INT);
INSERT INTO t VALUES (1,2,3),(2,3,NULL),(3,3,1);

CREATE TABLE places (id INT, postcode VARCHAR(10));
INSERT INTO places VALUES (1,'gb-1'),(2,'us-2'),(3,'gb-3');

CREATE TABLE my_table (column1 INT, column2 VARCHAR(40));
CREATE TABLE archive (id INT, name VARCHAR(40));
"""

# 有些题的「做题前状态」需要额外准备：题目本身是建表/改表，种子库里不能已经有它
SETUP = {
    "ddl_03": ["DROP TABLE CD"],
    "ddl_08": ["DROP TABLE branch"],
    "ddl_13": ["ALTER TABLE staff CHANGE COLUMN fName first_name VARCHAR(20) NOT NULL"],
    "ddl_14": ["ALTER TABLE staff ADD CONSTRAINT fk_staff_branch "
               "FOREIGN KEY (branchNo) REFERENCES branch(branchNo)"],
    "ddl_18": ["CREATE TABLE Persons (Id INT AUTO_INCREMENT PRIMARY KEY, "
               "lastname VARCHAR(255) NOT NULL, age INT DEFAULT 12)"],
    "ddl_01": ["DROP DATABASE IF EXISTS cpt103_lab2"],
    # 下面几道是第一批的老题：它们自己建表/加列，种子库里就得先没有
    "w_01": ["DROP TABLE books"],
    "w_02": ["DROP TABLE branch",
             "CREATE TABLE branch (branchNo CHAR(4) NOT NULL, "
             "postcode VARCHAR(10) DEFAULT NULL, PRIMARY KEY (branchNo))"],
    "w_05": ["ALTER TABLE staff DROP COLUMN salary"],
    "w_06": ["DROP TABLE staff"],
    "w_07": ["DROP TABLE authors_of_books"],
}


def connect(db=None):
    return pymysql.connect(unix_socket=SOCKET, user="root", database=db, autocommit=True)


def rebuild(conn):
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {DB}")
        cur.execute(f"CREATE DATABASE {DB}")
        cur.execute(f"USE {DB}")
        for stmt in [x.strip() for x in SEED.split(";") if x.strip()]:
            cur.execute(stmt)


def render(task, values):
    """把 parts 的行拼成一条语句，按顺序把 ____ 换成 values。"""
    lines = "\n".join("\n".join(p["lines"]) for p in task["parts"])
    out = lines
    for v in values:
        out = out.replace(BLANK, v, 1)
    return out


def variants(task):
    """为每个空生成 (说明, 取值列表)。每次只变一个空，其余取第一个可接受值。"""
    base = [b["accept"][0] for b in task["blanks"]]
    for i, b in enumerate(task["blanks"]):
        for alt in b["accept"]:
            vals = list(base)
            vals[i] = alt
            yield f"空{i + 1}={alt}", vals


def main():
    conn = connect()
    failures, warnings, total_runs = [], [], 0
    rows_report = []

    for task in SQL_TASKS:
        if task["kind"] != "blank":
            continue
        n_marks = "\n".join("\n".join(p["lines"]) for p in task["parts"]).count(BLANK)
        if n_marks != len(task["blanks"]):
            failures.append(f'{task["key"]}: 空位 {n_marks} 个，但 blanks 配了 {len(task["blanks"])} 个')
            continue

        for label, vals in variants(task):
            rebuild(conn)
            with conn.cursor() as cur:
                for stmt in SETUP.get(task["key"], []):
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        failures.append(f'{task["key"]}: 前置准备失败 {stmt!r} → {e}')
            sql = render(task, vals)
            total_runs += 1
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description:
                        rows = cur.fetchall()
                        rows_report.append((task["key"], label, len(rows)))
                        if not rows:
                            warnings.append(f'{task["key"]}: 能执行但 0 行（{label}）')
            except Exception as e:
                failures.append(f'{task["key"]} ({label}): {e}\n    {sql.replace(chr(10), " ")}')

    print(f"MySQL {conn.get_server_info()} · 执行 {total_runs} 次 · 语句 {sum(1 for t in SQL_TASKS if t['kind']=='blank')} 道")
    print()
    if rows_report:
        print("SELECT 类返回行数（用来确认没有「语法对但筛空」）：")
        for key, label, n in rows_report:
            mark = "✓" if n > 0 else "!"
            print(f"  {mark} {key:<9} {label:<16} {n} 行")
        print()
    if warnings:
        print(f"⚠ 警告 {len(warnings)}：")
        for w in warnings:
            print("  -", w)
        print()
    if warnings:
        failures.append(f"{len(warnings)} 条语句能执行但筛出 0 行")
    if failures:
        print(f"✗ 失败 {len(failures)}：")
        for f in failures:
            print("  -", f)
        conn.close()
        sys.exit(1)
    print("✓ 全部通过：每道题的每个可接受答案，在 MySQL 里都能执行")
    conn.close()


if __name__ == "__main__":
    main()
