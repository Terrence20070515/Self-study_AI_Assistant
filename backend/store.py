"""SQLite 存储：课程 / 资料 / 分块 / 聊天记录。全部数据都在 data/ 目录下。"""
import json
import os
import re
import sqlite3
import time
import unicodedata
import uuid

from .config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "study.db")


def fix_zip_name(name: str) -> str:
    """还原 zipfile 用 CP437 误解码出来的文件名。

    zip 条目没有 UTF-8 标志位时，Python 的 zipfile 按 CP437 解码文件名。
    macOS 的文件名是 NFD 形式（ó 存成 o + 组合音符），它的 UTF-8 字节 0xCC 0x81
    在 CP437 下正好是「╠ü」—— 于是 "Sesión" 变成 "Sesio╠ün" 一路存进库里，
    显示、搜索、导出拿到的都是乱码名。

    做法：把 str 编回 CP437 拿到原始字节，再按 UTF-8 解一次。两种情况原样返回，
    免得把本来正常的名字改坏：
      - CP437 编不出来（含中文等 CP437 之外的字符）→ 说明本来就是好的
      - 解出来不是合法 UTF-8 → 同上
    """
    if not name:
        return name
    try:
        raw = name.encode("cp437")
    except UnicodeEncodeError:
        return name
    try:
        fixed = raw.decode("utf-8")
    except UnicodeDecodeError:
        return name
    return unicodedata.normalize("NFC", fixed) if fixed != name else name


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS courses(
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                semester TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS materials(
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                orig_name TEXT NOT NULL,
                tag TEXT NOT NULL DEFAULT '其他',
                pages INTEGER DEFAULT 0,
                size INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT DEFAULT '',
                created_at REAL NOT NULL,
                deleted INTEGER NOT NULL DEFAULT 0,
                deleted_at REAL
            );
            CREATE TABLE IF NOT EXISTS chunks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                ord INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding BLOB
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_course ON chunks(course_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_material ON chunks(material_id);
            CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL
            );
            """
        )
        # 迁移：课程分组（major=专业课 / easy=水课 / elective=额外选修课）
        cols = [r["name"] for r in c.execute("PRAGMA table_info(courses)").fetchall()]
        if "course_group" not in cols:
            c.execute(
                "ALTER TABLE courses ADD COLUMN course_group TEXT NOT NULL DEFAULT 'major'"
            )
        # 迁移：资料文件类型（pdf / docx）
        cols = [r["name"] for r in c.execute("PRAGMA table_info(materials)").fetchall()]
        if "ext" not in cols:
            c.execute("ALTER TABLE materials ADD COLUMN ext TEXT NOT NULL DEFAULT 'pdf'")
        # 迁移：AI 入库分析结果（摘要 / 关键词 / 建议课程 / 是否已分析 / 标签是否人工锁定）
        cols = [r["name"] for r in c.execute("PRAGMA table_info(materials)").fetchall()]
        for col, ddl in (
            ("summary", "TEXT NOT NULL DEFAULT ''"),
            ("keywords", "TEXT NOT NULL DEFAULT ''"),
            ("ai_course", "TEXT NOT NULL DEFAULT ''"),
            ("ai_analyzed", "INTEGER NOT NULL DEFAULT 0"),
            ("tag_locked", "INTEGER NOT NULL DEFAULT 0"),
        ):
            if col not in cols:
                c.execute(f"ALTER TABLE materials ADD COLUMN {col} {ddl}")
        # 迁移：专业课学分（决定均分权重）
        cols = [r["name"] for r in c.execute("PRAGMA table_info(courses)").fetchall()]
        if "credits" not in cols:
            c.execute("ALTER TABLE courses ADD COLUMN credits REAL NOT NULL DEFAULT 0")
        # 成绩构成（Assessment Component）
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS assessments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                weight REAL NOT NULL DEFAULT 0,
                score REAL,
                ord INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_assessments_course ON assessments(course_id);
            """
        )
        # 沉浸模式逐页注释（一页可有多个语言版本，主键带上 lang）
        c.execute(
            """CREATE TABLE IF NOT EXISTS page_notes(
                material_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                lang TEXT NOT NULL DEFAULT 'zh',
                content TEXT NOT NULL,
                edited INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL,
                PRIMARY KEY(material_id, page, lang)
            )"""
        )
        # Word 段落批注：block_idx 是该文档 HTML 里顶层块的序号。
        # 和 page_notes 分开存 —— 那张表是「AI 逐页注释」（按 lang 分中/英/西），
        # 用户的批注混进去会被 AI 覆盖，语义也完全不同。
        c.execute(
            """CREATE TABLE IF NOT EXISTS block_notes(
                material_id TEXT NOT NULL,
                block_idx INTEGER NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                updated_at REAL NOT NULL,
                PRIMARY KEY(material_id, block_idx)
            )"""
        )
        # 待办事项（DDL + 具体事项；ord 为手动排序位；course_id 关联来源课程）
        c.execute(
            """CREATE TABLE IF NOT EXISTS todos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                due TEXT NOT NULL DEFAULT '',
                done INTEGER NOT NULL DEFAULT 0,
                ord INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                course_id TEXT NOT NULL DEFAULT ''
            )"""
        )
        # 练习题库：出过的题落库。题目有 id 才能记录作答、统计薄弱点、重练错题；
        # 不落库的话每次出题都是一次性消费，学习闭环就断在「答完即弃」。
        c.execute(
            """CREATE TABLE IF NOT EXISTS quiz_questions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'choice',
                question TEXT NOT NULL,
                options TEXT NOT NULL DEFAULT '[]',
                answer TEXT NOT NULL DEFAULT '',
                explanation TEXT NOT NULL DEFAULT '',
                refs TEXT NOT NULL DEFAULT '[]',
                unit_key TEXT NOT NULL DEFAULT '',
                level TEXT NOT NULL DEFAULT '',
                batch_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )"""
        )
        # 老库补齐批次列（出题批次：用来把「没做完的那一批」原样捞回来）
        _cols = {r["name"] for r in c.execute("PRAGMA table_info(quiz_questions)")}
        if "batch_id" not in _cols:
            c.execute("ALTER TABLE quiz_questions ADD COLUMN batch_id TEXT NOT NULL DEFAULT ''")
        c.execute("CREATE INDEX IF NOT EXISTS idx_quiz_course ON quiz_questions(course_id)")
        # 作答记录：每次作答都留痕（保留全部历史；薄弱点按「最近一次」判断）
        c.execute(
            """CREATE TABLE IF NOT EXISTS quiz_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL DEFAULT '',
                correct INTEGER NOT NULL DEFAULT 0,
                answered_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_attempt_q ON quiz_attempts(question_id)")
        # 汇编训练：每次提交都留档（代码 + 得分 + 批改 JSON），
        # 用来给题目列表标「已做/最好成绩」，也方便回头看自己怎么一步步改对的
        c.execute(
            """CREATE TABLE IF NOT EXISTS asm_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                task_key TEXT NOT NULL,
                code TEXT NOT NULL DEFAULT '',
                score INTEGER NOT NULL DEFAULT 0,
                feedback TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_asm_attempt ON asm_attempts(course_id, task_key)")
        # 专注记录：番茄钟以前只往 localStorage 写一个「今天几个」，
        # 没有课程、没有时长、跨天查不了，等于这个数字没法用来做任何分析。
        # 只记**完整走完**的（中途重置算放弃，不入库），否则误开的计时会污染统计。
        c.execute(
            """CREATE TABLE IF NOT EXISTS focus_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL DEFAULT '',
                minutes INTEGER NOT NULL DEFAULT 0,
                kind TEXT NOT NULL DEFAULT 'focus',
                at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_focus_at ON focus_sessions(at)")
        # 知识图：每门课一张，可长期维护。
        # 节点位置存像素坐标（前端世界坐标），parent_id=0 表示根节点。
        # AI 只负责起草原图，之后这张图是用户的 —— 拖动、改字、增删都直接写这里。
        c.execute(
            """CREATE TABLE IF NOT EXISTS kg_nodes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                material_id TEXT NOT NULL DEFAULT '',
                page INTEGER NOT NULL DEFAULT 0,
                parent_id INTEGER NOT NULL DEFAULT 0,
                x REAL NOT NULL DEFAULT 0,
                y REAL NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_kg_node_course ON kg_nodes(course_id)")
        # 连线是自由的，但必须带类型（属于 / 依赖 / 对比）——
        # 无名线过一个月连自己都看不懂是什么意思。
        c.execute(
            """CREATE TABLE IF NOT EXISTS kg_edges(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                kind TEXT NOT NULL DEFAULT 'belongs',
                created_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_kg_edge_course ON kg_edges(course_id)")
        # 速查表：每门课一份，四段（术语 / 公式 / 代码 / 易错点）。
        # 应用内可编辑，同一份内容另出一条 PDF 出口 —— PDF 是终点，能改的页面才是过程。
        c.execute(
            """CREATE TABLE IF NOT EXISTS cheat_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                section TEXT NOT NULL DEFAULT 'terms',
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                material_id TEXT NOT NULL DEFAULT '',
                page INTEGER NOT NULL DEFAULT 0,
                ord INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_cheat_course ON cheat_items(course_id)")
        # 覆盖率台账：记录每个知识点单元是否出过题。
        # unit_key 由「资料 + 页 + 段号」拼成（见 core.build_knowledge_units）——
        # 只要资料内容不变，同一页永远算出同一个 key，覆盖率才能跨次累积。
        c.execute(
            """CREATE TABLE IF NOT EXISTS quiz_coverage(
                unit_key TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                material_id TEXT NOT NULL,
                page INTEGER NOT NULL DEFAULT 0,
                question_cnt INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_coverage_course ON quiz_coverage(course_id)")
        # 阅读进度（每份资料读到第几页）
        c.execute(
            """CREATE TABLE IF NOT EXISTS material_progress(
                material_id TEXT PRIMARY KEY,
                page INTEGER NOT NULL DEFAULT 1,
                updated_at REAL NOT NULL
            )"""
        )
        # 文件笔记（学生在阅读时自己写的笔记）
        c.execute(
            """CREATE TABLE IF NOT EXISTS material_my_notes(
                material_id TEXT PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                updated_at REAL NOT NULL
            )"""
        )
        # 页面圈画：每页一组笔画（坐标按页面宽高归一化，缩放/适应宽度都不错位）
        c.execute(
            """CREATE TABLE IF NOT EXISTS page_ink(
                material_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                data TEXT NOT NULL DEFAULT '[]',
                updated_at REAL NOT NULL,
                PRIMARY KEY(material_id, page)
            )"""
        )
        # 本页批注：每页一组文本块（标题 / 正文两种样式）
        c.execute(
            """CREATE TABLE IF NOT EXISTS page_mynotes(
                material_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                blocks TEXT NOT NULL DEFAULT '[]',
                updated_at REAL NOT NULL,
                PRIMARY KEY(material_id, page)
            )"""
        )
    _migrate()

    # ---------- 老库迁移：补列 / 补默认值 ----------

def _migrate():
    with _conn() as c:
        cols = {r["name"] for r in c.execute("PRAGMA table_info(todos)").fetchall()}
        if "ord" not in cols:                      # 老库补 ord，按 id 顺序初始化
            c.execute("ALTER TABLE todos ADD COLUMN ord INTEGER NOT NULL DEFAULT 0")
            c.execute("UPDATE todos SET ord = id")
        if "course_id" not in cols:                # 老库补课程归属（'' = 不属于任何课程）
            c.execute("ALTER TABLE todos ADD COLUMN course_id TEXT NOT NULL DEFAULT ''")
        # 老库补台账关联列（'' = 这道题没记知识点，不计入覆盖率）
        qcols = {r["name"] for r in c.execute("PRAGMA table_info(quiz_questions)").fetchall()}
        if qcols and "unit_key" not in qcols:
            c.execute("ALTER TABLE quiz_questions ADD COLUMN unit_key TEXT NOT NULL DEFAULT ''")
        # 题目难度标签（easy/medium/hard）；老库补列，已有题为空串，前端不显示
        if qcols and "level" not in qcols:
            c.execute("ALTER TABLE quiz_questions ADD COLUMN level TEXT NOT NULL DEFAULT ''")
        # 从未排过序（全为 0）时按 id 初始化一次
        if c.execute("SELECT COUNT(*) AS n FROM todos WHERE ord != 0").fetchone()["n"] == 0:
            c.execute("UPDATE todos SET ord = id")

        # page_notes 老库没有 lang 列 → 重建表（SQLite 改不了主键）。
        # 已有注释全部认定为中文 —— 这几百上千条是用户看着读过的，一条都不能丢。
        pncols = {r["name"] for r in c.execute("PRAGMA table_info(page_notes)").fetchall()}
        if pncols and "lang" not in pncols:
            c.execute(
                """CREATE TABLE page_notes_v2(
                    material_id TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    lang TEXT NOT NULL DEFAULT 'zh',
                    content TEXT NOT NULL,
                    edited INTEGER NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(material_id, page, lang)
                )"""
            )
            c.execute(
                "INSERT INTO page_notes_v2(material_id, page, lang, content, edited, updated_at)"
                " SELECT material_id, page, 'zh', content, edited, updated_at FROM page_notes"
            )
            c.execute("DROP TABLE page_notes")
            c.execute("ALTER TABLE page_notes_v2 RENAME TO page_notes")


# 合法列名：小写字母或下划线开头，只含小写字母 / 数字 / 下划线
_SAFE_COL = re.compile(r"^[a-z_][a-z0-9_]*$")


def _check_fields(fields: dict, allowed: set, table: str):
    """更新列名的双重校验：非法字段直接报错，而不是拼进 SQL。

    第一道：白名单 —— 只允许代码里写死的列名（防的是调用方传错/传恶意字段）。
    第二道：格式 —— 即使将来白名单被误改宽，也能挡住 `a; DROP TABLE` 这类列名。
    值本身始终走参数绑定，这里只管列名。
    """
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"{table} 不允许更新字段：{sorted(bad)}")
    for k in fields:
        if not _SAFE_COL.match(str(k)):
            raise ValueError(f"{table} 非法字段名：{k!r}")


def now() -> float:
    return time.time()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------- courses ----------

def list_courses():
    with _conn() as c:
        rows = c.execute(
            """SELECT co.*, (SELECT COUNT(*) FROM materials m
                             WHERE m.course_id=co.id AND m.deleted=0) AS material_count
               FROM courses co ORDER BY co.created_at"""
        ).fetchall()
        return [dict(r) for r in rows]


def create_course(code: str, name: str, semester: str, group: str = "major"):
    cid = new_id()
    with _conn() as c:
        c.execute(
            "INSERT INTO courses(id, code, name, semester, course_group, created_at) VALUES(?,?,?,?,?,?)",
            (cid, code.strip(), name.strip(), semester.strip(), group, now()),
        )
    return cid


# 各表允许更新的列（白名单）。防止把用户输入当成列名拼进 SQL：
# 值走参数绑定是安全的，但列名只能来自代码里写死的集合。
COURSE_FIELDS = {"name", "semester", "course_group", "credits", "code"}


def update_course(cid: str, **fields):
    _check_fields(fields, COURSE_FIELDS, "courses")
    keys = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE courses SET {keys} WHERE id=?", (*fields.values(), cid))


def get_course(cid: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None


def find_course_by_code(code: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM courses WHERE code=?", (code.strip(),)).fetchone()
        return dict(r) if r else None


def get_or_create_course(code: str, name: str = "", semester: str = ""):
    course = find_course_by_code(code)
    if course:
        return course
    cid = create_course(code, name, semester)
    return get_course(cid)


def delete_course(cid: str):
    """删除课程：资料进回收区，聊天记录清除。"""
    ts = now()
    with _conn() as c:
        c.execute(
            "UPDATE materials SET deleted=1, deleted_at=? WHERE course_id=? AND deleted=0",
            (ts, cid),
        )
        c.execute("DELETE FROM messages WHERE course_id=?", (cid,))
        c.execute("DELETE FROM courses WHERE id=?", (cid,))


# ---------- materials ----------

def add_material(course_id: str, orig_name: str, tag: str, size: int, ext: str = "pdf") -> str:
    mid = new_id()
    with _conn() as c:
        c.execute(
            "INSERT INTO materials(id, course_id, orig_name, tag, size, ext, created_at) VALUES(?,?,?,?,?,?,?)",
            (mid, course_id, orig_name, tag, size, ext, now()),
        )
    return mid


MATERIAL_FIELDS = {"tag", "status", "error", "pages", "course_id", "deleted", "deleted_at",
                   "summary", "keywords", "ai_course", "ai_analyzed", "tag_locked"}


def update_material(mid: str, **fields):
    _check_fields(fields, MATERIAL_FIELDS, "materials")
    keys = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE materials SET {keys} WHERE id=?", (*fields.values(), mid))


def get_material(mid: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        return dict(r) if r else None


def set_material_tags(ids: list, tag: str) -> int:
    """批量改标签。

    tag 非空 → `tag_locked=1`，后续「AI 整理」不再覆盖人工判断；
    tag 为空 → 清空并解锁，下次 AI 分析可以重新猜。
    一次 executemany 写同一个事务，避免半批成功半批失败。
    """
    ids = [i for i in (ids or []) if i]
    if not ids:
        return 0
    locked = 0 if not tag else 1
    with _conn() as c:
        c.executemany(
            "UPDATE materials SET tag=?, tag_locked=? WHERE id=? AND deleted=0",
            [(tag, locked, i) for i in ids],
        )
    return len(ids)


def list_materials(course_id: str, query: str = "", deleted: int = 0):
    sql = """SELECT m.*, (SELECT COUNT(DISTINCT pn.page) FROM page_notes pn WHERE pn.material_id=m.id) AS notes_count
             FROM materials m WHERE m.course_id=? AND deleted=?"""
    args = [course_id, deleted]
    if query:
        sql += " AND orig_name LIKE ?"
        args.append(f"%{query}%")
    sql += " ORDER BY created_at DESC"
    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
        return [dict(r) for r in rows]


def pending_analysis(course_id: str = ""):
    """还没做过入库 AI 分析的资料（只算解析成功的，避免对失败资料白调 AI）。"""
    sql = """SELECT id, orig_name FROM materials
             WHERE deleted=0 AND ai_analyzed=0 AND status='ready'"""
    args: list = []
    if course_id:
        sql += " AND course_id=?"
        args.append(course_id)
    sql += " ORDER BY created_at"
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def soft_delete_material(mid: str):
    with _conn() as c:
        c.execute(
            "UPDATE materials SET deleted=1, deleted_at=? WHERE id=?", (now(), mid)
        )


def restore_material(mid: str):
    with _conn() as c:
        c.execute("UPDATE materials SET deleted=0, deleted_at=NULL WHERE id=?", (mid,))


def move_material(mid: str, course_id: str):
    with _conn() as c:
        c.execute("UPDATE materials SET course_id=? WHERE id=?", (course_id, mid))
        c.execute("UPDATE chunks SET course_id=? WHERE material_id=?", (course_id, mid))


# ---------- 待办事项 ----------

def list_todos():
    """按手动顺序（ord）返回；未排序过的按 id。未完成/已完成的分组交给前端。

    同时带出 course_code / course_name —— 待办列表要能一眼看出「这条属于哪门课」，
    否则从 HandBook 扫进来的 DDL 会分不清是哪一科。
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT t.*, COALESCE(c.code,'') AS course_code, COALESCE(c.name,'') AS course_name"
            " FROM todos t LEFT JOIN courses c ON c.id = t.course_id"
            " ORDER BY CASE WHEN t.ord=0 THEN t.id ELSE t.ord END ASC, t.id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def reorder_todos(ids: list):
    """按传入顺序写入 ord（一次提交，避免 N 次往返）。"""
    with _conn() as c:
        c.executemany("UPDATE todos SET ord=? WHERE id=?",
                      [(i, int(tid)) for i, tid in enumerate(ids, start=1)])


def add_todo(content: str, due: str, course_id: str = ""):
    with _conn() as c:
        c.execute(
            "INSERT INTO todos(content, due, course_id, created_at) VALUES(?,?,?,?)",
            (content.strip(), due or "", course_id or "", now()),
        )


TODO_FIELDS = {"content", "due", "done", "ord", "course_id"}


def update_todo(todo_id: int, **fields):
    _check_fields(fields, TODO_FIELDS, "todos")
    keys = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE todos SET {keys} WHERE id=?", (*fields.values(), todo_id))


# ---------- 阅读进度 ----------

def get_progress(material_id: str) -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT page FROM material_progress WHERE material_id=?", (material_id,)
        ).fetchone()
        return int(row["page"]) if row else 0


def set_progress(material_id: str, page: int):
    with _conn() as c:
        c.execute(
            """INSERT INTO material_progress(material_id, page, updated_at) VALUES(?,?,?)
               ON CONFLICT(material_id) DO UPDATE SET page=excluded.page, updated_at=excluded.updated_at""",
            (material_id, int(page), now()),
        )


def latest_progress() -> dict | None:
    """最近读过的那份资料（供主页「继续上次」用）。"""
    with _conn() as c:
        row = c.execute(
            """SELECT p.material_id, p.page, p.updated_at, m.orig_name, m.ext,
                      m.course_id, co.code AS course_code
               FROM material_progress p
               JOIN materials m ON m.id = p.material_id
               LEFT JOIN courses co ON co.id = m.course_id
               WHERE m.deleted = 0
               ORDER BY p.updated_at DESC LIMIT 1"""
        ).fetchone()
        return dict(row) if row else None


# ---------- 文件笔记（自己写的） ----------

def get_my_note(material_id: str) -> str:
    with _conn() as c:
        row = c.execute(
            "SELECT content FROM material_my_notes WHERE material_id=?", (material_id,)
        ).fetchone()
        return row["content"] if row else ""


def set_my_note(material_id: str, content: str):
    with _conn() as c:
        c.execute(
            """INSERT INTO material_my_notes(material_id, content, updated_at) VALUES(?,?,?)
               ON CONFLICT(material_id) DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at""",
            (material_id, content, now()),
        )


# ---------- 页面圈画 ----------

def get_ink(material_id: str, page: int) -> str:
    """该页笔画的 JSON 字符串（没有则返回空数组）。"""
    with _conn() as c:
        row = c.execute(
            "SELECT data FROM page_ink WHERE material_id=? AND page=?",
            (material_id, int(page)),
        ).fetchone()
        return row["data"] if row else "[]"


def set_ink(material_id: str, page: int, data: str):
    with _conn() as c:
        c.execute(
            """INSERT INTO page_ink(material_id, page, data, updated_at) VALUES(?,?,?,?)
               ON CONFLICT(material_id, page) DO UPDATE SET
                 data=excluded.data, updated_at=excluded.updated_at""",
            (material_id, int(page), data, now()),
        )


def marked_pages(material_id: str) -> dict:
    """哪些页有圈画，供页面标记使用。"""
    with _conn() as c:
        ink = [r["page"] for r in c.execute(
            "SELECT page FROM page_ink WHERE material_id=? AND data NOT IN ('[]', '')",
            (material_id,)).fetchall()]
    return {"ink": sorted(ink)}


# ---------- 沉浸模式逐页注释 ----------

def get_block_notes(material_id: str) -> dict:
    """该 Word 文档的所有段落批注：{block_idx: content}。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT block_idx, content FROM block_notes WHERE material_id=?",
            (material_id,),
        ).fetchall()
    return {int(r["block_idx"]): r["content"] for r in rows}


def set_block_note(material_id: str, block_idx: int, content: str):
    """写或清空某一段的批注（content 为空即删除）。"""
    content = (content or "").strip()
    with _conn() as c:
        if content:
            c.execute(
                "INSERT INTO block_notes(material_id, block_idx, content, updated_at)"
                " VALUES(?,?,?,?)"
                " ON CONFLICT(material_id, block_idx)"
                " DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at",
                (material_id, block_idx, content, now()),
            )
        else:
            c.execute(
                "DELETE FROM block_notes WHERE material_id=? AND block_idx=?",
                (material_id, block_idx),
            )


def get_notes(material_id: str, lang: str = "zh"):
    """取某份资料某语言的逐页注释（默认中文）。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT page, content, edited FROM page_notes"
            " WHERE material_id=? AND lang=? ORDER BY page",
            (material_id, lang),
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_note(material_id: str, page: int, content: str,
                edited: int = 0, lang: str = "zh"):
    with _conn() as c:
        c.execute(
            """INSERT INTO page_notes(material_id, page, lang, content, edited, updated_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(material_id, page, lang) DO UPDATE SET
                 content=excluded.content, edited=excluded.edited, updated_at=excluded.updated_at""",
            (material_id, page, lang, content, edited, now()),
        )


def materials_with_course(query: str = "", tag: str = "", deleted: int = 0):
    """跨课程查询资料（回收区 / 资料总库共用），SQL 收口在数据层。"""
    sql = """SELECT m.*, co.code AS course_code, co.name AS course_name,
                    (SELECT COUNT(DISTINCT pn.page) FROM page_notes pn WHERE pn.material_id=m.id) AS notes_count
             FROM materials m LEFT JOIN courses co ON co.id = m.course_id
             WHERE m.deleted=?"""
    args = [deleted]
    if query.strip():
        sql += " AND m.orig_name LIKE ?"
        args.append(f"%{query.strip()}%")
    if tag.strip():
        sql += " AND m.tag = ?"
        args.append(tag.strip())
    sql += " ORDER BY m.created_at DESC" if not deleted else " ORDER BY m.deleted_at DESC"
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def delete_todo(todo_id: int):
    with _conn() as c:
        c.execute("DELETE FROM todos WHERE id=?", (todo_id,))


# ---------- 练习：题库 / 作答 / 薄弱点 ----------
# 这一层是学习闭环的后半段：出题 → 作答 → 判分 → 累积薄弱点 → 只重练错过的。

def _quiz_row(r) -> dict:
    """把库里的行转成题目对象（options / refs 是 JSON 文本，这里还原）。"""
    d = dict(r)
    for k in ("options", "refs"):
        try:
            d[k] = json.loads(d.get(k) or "[]")
        except (TypeError, ValueError):
            d[k] = []
    return d


def save_quiz_questions(course_id: str, questions: list, batch_id: str = "") -> list:
    """一次出题的题目全部落库，返回带 id 的题目列表（前端靠 id 提交作答）。

    题目与覆盖率台账**写在同一个事务里** —— 题存了但台账漏记，覆盖率就会偏低，
    而这种偏差在界面上是「明明练过却说自己没覆盖」，很难被发现。

    `batch_id`：一次出题用一个批次号。没做完的那批可以整批原样捞回来接着做
    （以前只有「是否作答过」这一个维度，退出界面那批就找不回来了）。
    """
    batch = (batch_id or "").strip() or f"b{uuid.uuid4().hex[:12]}"
    out = []
    with _conn() as c:
        for q in questions or []:
            opts = q.get("options") or []
            # 出题侧不返回 kind，这里按有无选项判定（选择题才有选项）
            kind = str(q.get("kind") or ("choice" if opts else "short"))
            unit_key = str(q.get("unit_key") or "")
            level = str(q.get("level") or "").lower()
            if level not in ("easy", "medium", "hard"):   # 模型偶尔给别的词，存空表示未标注
                level = ""
            cur = c.execute(
                "INSERT INTO quiz_questions(course_id, kind, question, options, answer,"
                " explanation, refs, unit_key, level, batch_id, created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    course_id,
                    kind,
                    str(q.get("question") or ""),
                    json.dumps(opts, ensure_ascii=False),
                    str(q.get("answer") or ""),
                    str(q.get("explanation") or ""),
                    json.dumps(q.get("refs") or [], ensure_ascii=False),
                    unit_key,
                    level,
                    batch,
                    now(),
                ),
            )
            item = dict(q)
            item["id"] = cur.lastrowid
            item["kind"] = kind
            item["batch_id"] = batch
            out.append(item)

        for q in questions or []:
            uk = str(q.get("unit_key") or "")
            if not uk:
                continue                      # 没有知识点归属的题（如纯抽题）不计入覆盖率
            c.execute(
                "INSERT INTO quiz_coverage(unit_key, course_id, material_id, page,"
                " question_cnt, updated_at) VALUES(?,?,?,?,1,?)"
                " ON CONFLICT(unit_key) DO UPDATE SET"
                " question_cnt = question_cnt + 1, updated_at = excluded.updated_at",
                (uk, course_id, str(q.get("material_id") or ""),
                 int(q.get("page") or 0), now()),
            )
    return out


def covered_unit_keys(course_id: str) -> set:
    """该课程已出过题的知识点单元集合（覆盖率分子）。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT unit_key FROM quiz_coverage WHERE course_id=? AND question_cnt>0",
            (course_id,),
        ).fetchall()
        return {r["unit_key"] for r in rows}


def coverage_counts(course_id: str) -> dict:
    """每个知识点单元出过几道题。复用时优先挑出得少的 ——
    实测有页被抽了 8 次全是同一个知识点，因为那份资料已经刷满、只能复用。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT unit_key, question_cnt FROM quiz_coverage WHERE course_id=?",
            (course_id,),
        ).fetchall()
    return {r["unit_key"]: int(r["question_cnt"] or 0) for r in rows}


def coverage_stats(course_id: str) -> dict:
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(question_cnt),0) AS q FROM quiz_coverage"
            " WHERE course_id=? AND question_cnt>0",
            (course_id,),
        ).fetchone()
    return {"covered": row["n"], "covered_questions": int(row["q"] or 0)}


def coverage_by_material(course_id: str) -> dict:
    """按资料聚合已覆盖的单元数（总数由调用方按 chunk 字数算）。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT material_id, COUNT(*) AS n FROM quiz_coverage"
            " WHERE course_id=? AND question_cnt>0 GROUP BY material_id",
            (course_id,),
        ).fetchall()
        return {r["material_id"]: int(r["n"]) for r in rows}


def get_quiz_question(qid: int):
    with _conn() as c:
        r = c.execute("SELECT * FROM quiz_questions WHERE id=?", (int(qid),)).fetchone()
        return _quiz_row(r) if r else None


def record_attempt(question_id: int, user_answer: str, correct: bool):
    """记录一次作答。历史全留（同一题多次作答都存），薄弱点按最近一次判断。"""
    with _conn() as c:
        c.execute(
            "INSERT INTO quiz_attempts(question_id, user_answer, correct, answered_at)"
            " VALUES(?,?,?,?)",
            (int(question_id), str(user_answer or ""), 1 if correct else 0, now()),
        )


def _latest_attempt_join():
    """只取每题「最近一次」作答的 JOIN 片段（用 MAX(id) 定位，比时间戳稳）。"""
    return (
        " JOIN quiz_attempts a ON a.id ="
        " (SELECT id FROM quiz_attempts WHERE question_id=q.id ORDER BY id DESC LIMIT 1)"
    )


def list_wrong_questions(course_id: str, limit: int = 50) -> list:
    """薄弱点：最近一次作答是错的题（后续答对了就不再出现）。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT q.*, a.user_answer, a.answered_at,"
            " (SELECT COUNT(*) FROM quiz_attempts x WHERE x.question_id=q.id) AS attempts"
            " FROM quiz_questions q" + _latest_attempt_join() +
            " WHERE q.course_id=? AND a.correct=0"
            " ORDER BY a.id DESC LIMIT ?",
            (course_id, int(limit)),
        ).fetchall()
        return [_quiz_row(r) for r in rows]


def quiz_stats(course_id: str) -> dict:
    """练习统计：出题数、已答数、答对率、待重练数。"""
    with _conn() as c:
        total_q = c.execute(
            "SELECT COUNT(*) AS n FROM quiz_questions WHERE course_id=?", (course_id,)
        ).fetchone()["n"]
        row = c.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(a.correct),0) AS ok FROM quiz_questions q"
            + _latest_attempt_join() +
            " WHERE q.course_id=?", (course_id,)
        ).fetchone()
        answered, ok = row["n"], int(row["ok"] or 0)
        wrong = c.execute(
            "SELECT COUNT(*) AS n FROM quiz_questions q" + _latest_attempt_join() +
            " WHERE q.course_id=? AND a.correct=0", (course_id,)
        ).fetchone()["n"]
        # 一次都没答过的题 = 没做完的。界面上「出题 N / 已做 M」那种数字没意义
        # （出了题本来就该做），真正要显示的是「还剩几道」
        pending = c.execute(
            "SELECT COUNT(*) AS n FROM quiz_questions q WHERE q.course_id=?"
            " AND NOT EXISTS (SELECT 1 FROM quiz_attempts a WHERE a.question_id=q.id)",
            (course_id,),
        ).fetchone()["n"]
    return {
        "questions": total_q,
        "answered": answered,
        "correct": ok,
        "accuracy": round(ok * 100 / answered, 1) if answered else None,
        "wrong": wrong,
        "pending": pending,
    }


# ---------- 未完成的练习（按出题批次归档） ----------

_BATCH_KEY_SQL = (
    "CASE WHEN q.batch_id<>'' THEN q.batch_id"
    " ELSE 'legacy-' || CAST(q.created_at/60 AS INTEGER) END"
)


def list_pending_batches(course_id: str, limit: int = 30) -> dict:
    """没做过的题，按出题批次归堆 —— 中途退出后还能整批捞回来接着做。

    「没做过」= **一条作答记录都没有**。答错过的题不在这里（那些在错题本里），
    所以做完一道就自动从本批减一，全做完这批就消失。

    老数据没有 batch_id（这个字段是后加的），用「创建时间落在同一分钟」当一批：
    一次出题是同步落库的，几十道题都在同一分钟内完成。
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT q.*, " + _BATCH_KEY_SQL + " AS batch_key"
            " FROM quiz_questions q"
            " WHERE q.course_id=?"
            "   AND NOT EXISTS (SELECT 1 FROM quiz_attempts a WHERE a.question_id=q.id)"
            " ORDER BY q.created_at DESC, q.id DESC",
            (course_id,),
        ).fetchall()

    groups: dict[str, dict] = {}
    for r in rows:
        q = _quiz_row(r)
        key = q.pop("batch_key")
        g = groups.setdefault(key, {"batch_id": key, "created_at": q["created_at"],
                                    "questions": []})
        g["questions"].append(q)

    out = sorted(groups.values(), key=lambda g: -g["created_at"])
    for g in out:
        g["count"] = len(g["questions"])
        names, seen = [], set()
        for q in g["questions"]:
            for ref in (q.get("refs") or []):
                n = ref.get("orig_name") or ""
                if n and n not in seen:
                    seen.add(n)
                    names.append(n)
        g["materials"] = names[:3]
    return {"total": len(rows), "batch_count": len(out), "batches": out[:limit]}


# ---------- 全库内容搜索（词面） ----------
# 语义那半条在 core.search_content_semantic —— 它要跑 embedding，
# 放这里会让 store 依赖模型调用，而 store 现在还是纯数据层。

_SNIPPET_PAD = 70      # 片段左右各取多少字
_MAX_SCAN = 3000       # LIKE 最多捞多少块回来打分（全库 16767 块，通常只命中几十到几百）


def _search_terms(query: str) -> list[str]:
    """把查询拆成检索词。

    中文不切词（本机没有分词器），按空格与标点切；
    切不动的整串当一个词，靠 LIKE 子串匹配也能命中中文短语。
    """
    raw = re.split(r"[\s,，.。;；:：!！?？、/\\|()（）\[\]【】<>《》\"'“”‘’]+", query or "")
    out, seen = [], set()
    for t in raw:
        t = t.strip()
        if not t:
            continue
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(t)
    return out[:8]          # 词太多等于要求「全部命中」，实测 3 个以内最好用


def _make_snippet(text: str, terms: list[str]) -> tuple[str, list[str]]:
    """截命中词附近的一段，并返回真正出现过的词（前端用来高亮）。"""
    low = (text or "").lower()
    hit_at, hit_terms = -1, []
    for t in terms:
        i = low.find(t.lower())
        if i >= 0:
            hit_terms.append(t)
            if hit_at < 0 or i < hit_at:
                hit_at = i
    if hit_at < 0:
        return (text or "")[:_SNIPPET_PAD * 2], hit_terms
    lo = max(0, hit_at - _SNIPPET_PAD)
    hi = min(len(text), hit_at + _SNIPPET_PAD)
    frag = text[lo:hi].replace("\n", " ")
    return ("…" if lo > 0 else "") + frag + ("…" if hi < len(text) else ""), hit_terms


def search_content_word(query: str, limit: int = 40) -> dict:
    """全库词面搜索：命中 `chunks.text`，按「命中词数 → 出现次数」排序。

    同一页只留一条 —— 滑窗把一页切成多块，同页会重复命中。
    先要求所有词都命中；全不中再放宽成「命中任意词」并标 partial，
    否则搜「外键 级联」这种多词查询会直接空手而归。
    """
    terms = _search_terms(query)
    if not terms:
        return {"hits": [], "partial": False, "scanned": 0}

    def run(and_mode: bool) -> list:
        joiner = " AND " if and_mode else " OR "
        where = joiner.join(["c.text LIKE ?"] * len(terms))
        sql = (
            "SELECT c.material_id, c.page, c.ord, c.text, m.orig_name, m.ext, m.course_id"
            " FROM chunks c JOIN materials m ON m.id = c.material_id"
            " WHERE m.deleted = 0 AND (" + where + ")"
            " LIMIT ?"
        )
        params = [f"%{t}%" for t in terms] + [_MAX_SCAN]
        with _conn() as conn:
            return conn.execute(sql, params).fetchall()

    rows = run(True)
    partial = False
    if not rows:
        rows, partial = run(False), True
    if not rows:
        return {"hits": [], "partial": False, "scanned": 0}

    scored = []
    for r in rows:
        low = (r["text"] or "").lower()
        # 命中词数优先：全中的一条永远排在只中一个词的前面
        kinds = sum(1 for t in terms if t.lower() in low)
        count = sum(low.count(t.lower()) for t in terms)
        scored.append((kinds, count, r))
    scored.sort(key=lambda x: (-x[0], -x[1]))

    hits, seen_pages = [], set()
    for kinds, _count, r in scored:
        key = (r["material_id"], r["page"])
        if key in seen_pages:
            continue
        seen_pages.add(key)
        snippet, hit_terms = _make_snippet(r["text"], terms)
        hits.append({
            "material_id": r["material_id"],
            "orig_name": r["orig_name"],
            "ext": r["ext"] or "pdf",
            "page": r["page"],
            "snippet": snippet,
            "terms": hit_terms,
            "matched": kinds,
        })
        if len(hits) >= limit:
            break
    return {"hits": hits, "partial": partial, "scanned": len(rows)}


# ---------- 错题本（跨课程） ----------

def _question_page(q: dict) -> int | None:
    """这道题对应资料的哪一页。unit_key 形如 `<material_id>#p14`。"""
    m = re.search(r"#p(\d+)", q.get("unit_key") or "")
    if m:
        return int(m.group(1))
    for r in (q.get("refs") or []):
        if isinstance(r, dict) and r.get("n"):
            try:
                return int(r["n"])
            except (TypeError, ValueError):
                pass
    return None


def _question_material(q: dict) -> tuple[str, str]:
    """(material_id, 资料名)。refs 里带着出处，比 unit_key 更全。"""
    mid = (q.get("unit_key") or "").split("#")[0].strip()
    for r in (q.get("refs") or []):
        if isinstance(r, dict) and r.get("material_id"):
            return (mid or str(r["material_id"])), (r.get("orig_name") or "")
    return mid or "", ""


def list_wrong_all(limit_per_course: int = 300) -> list[dict]:
    """全部课程的错题，按「课程 → 资料」分组。

    判定沿用 list_wrong_questions：**最近一次作答仍错**。答对一次就从这里消失，
    所以它是「待解决清单」而不是历史台账 —— 重做对了自然会掉出列表。
    """
    out = []
    for co in list_courses():
        qs = list_wrong_questions(co["id"], limit=limit_per_course)
        if not qs:
            continue
        # 一次取出本课资料的 ext：前端点「去原文」要按 ext 选阅读器
        with _conn() as c:
            ext_of = {r["id"]: r["ext"] for r in c.execute(
                "SELECT id, ext FROM materials WHERE course_id=?", (co["id"],)).fetchall()}
        buckets: dict[str, dict] = {}
        for q in qs:
            mid, name = _question_material(q)
            page = _question_page(q)
            b = buckets.setdefault(mid, {"material_id": mid, "orig_name": name,
                                         "ext": ext_of.get(mid, "pdf"),
                                         "page": page, "questions": []})
            if not b["orig_name"] and name:
                b["orig_name"] = name
            if b["page"] is None and page is not None:
                b["page"] = page
            b["questions"].append({
                "id": q["id"], "kind": q.get("kind"), "level": q.get("level"),
                "question": q.get("question"), "options": q.get("options") or [],
                "answer": q.get("answer"), "explanation": q.get("explanation"),
                "user_answer": q.get("user_answer"), "answered_at": q.get("answered_at"),
                "attempts": q.get("attempts"), "page": page, "material_id": mid,
            })
        mats = sorted(buckets.values(), key=lambda x: -len(x["questions"]))
        out.append({"course_id": co["id"], "course_code": co["code"],
                    "course_name": co["name"], "count": len(qs), "materials": mats})
    out.sort(key=lambda x: -x["count"])
    return out


# ---------- 薄弱点排行 ----------
# 错题本按「错了几道」排序，缺的是分母：错 7 道可能是从 8 道里错的（基本没掌握），
# 也可能是从 40 道里错的（其实还行）。这两者在错题本里长得一模一样，
# 但复习优先级完全不同 —— 所以要按正确率另排一次。

MIN_SAMPLE = 3          # 答过少于这个数不参与排名（错 1 道 = 0%，会把排行榜冲垮）


def weak_points(limit: int = 8) -> dict:
    """按资料的正确率排行，取「最该补的 N 处」。

    口径与错题本一致：每题只算**最近一次**作答。
    只统计还有错题的资料（全对的不需要复习）。
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT substr(q.unit_key, 1, instr(q.unit_key, '#') - 1) AS mid,"
            " COUNT(*) AS answered, COALESCE(SUM(a.correct), 0) AS ok"
            " FROM quiz_questions q" + _latest_attempt_join() +
            " WHERE q.unit_key <> '' AND instr(q.unit_key, '#') > 0"
            " GROUP BY mid"
        ).fetchall()

    if not rows:
        return {"items": [], "low_sample": 0, "min_sample": MIN_SAMPLE}

    ids = [r["mid"] for r in rows if r["mid"]]
    if not ids:
        return {"items": [], "low_sample": 0, "min_sample": MIN_SAMPLE}
    with _conn() as c:
        info = {r["id"]: r for r in c.execute(
            "SELECT m.id, m.orig_name, m.ext, m.deleted, m.course_id, co.code AS course_code"
            " FROM materials m LEFT JOIN courses co ON co.id = m.course_id"
            " WHERE m.id IN (" + ",".join("?" * len(ids)) + ")", ids).fetchall()}

    items, low = [], 0
    for r in rows:
        mid, answered, ok = r["mid"], r["answered"], int(r["ok"] or 0)
        m = info.get(mid)
        if not m or m["deleted"]:
            continue
        wrong = answered - ok
        if wrong <= 0:
            continue                       # 全对，不用复习
        if answered < MIN_SAMPLE:
            low += 1                       # 样本太少，只统计不排名
            continue
        items.append({
            "material_id": mid,
            "orig_name": m["orig_name"],
            "ext": m["ext"] or "pdf",
            "course_id": m["course_id"],
            "course_code": m["course_code"] or "",
            "answered": answered,
            "correct": ok,
            "wrong": wrong,
            "accuracy": round(ok * 100 / answered, 1),
        })

    # 正确率低的优先；同率时错题多的优先（同样 50%，错 12 道比错 2 道更值得补）
    items.sort(key=lambda x: (x["accuracy"], -x["wrong"]))
    return {"items": items[:limit], "low_sample": low, "min_sample": MIN_SAMPLE}


# ---------- 专注记录（番茄钟） ----------

def add_focus_session(course_id: str, minutes: int, kind: str = "focus") -> dict:
    """记一次完整走完的番茄。中途重置的不该调到这里。"""
    kind = "break" if str(kind).lower() == "break" else "focus"
    minutes = max(1, min(int(minutes or 0), 24 * 60))
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO focus_sessions(course_id, minutes, kind, at) VALUES(?,?,?,?)",
            (course_id or "", minutes, kind, now()),
        )
        return {"id": cur.lastrowid, "course_id": course_id or "",
                "minutes": minutes, "kind": kind}


def focus_summary(days: int = 7) -> dict:
    """今日 / 近 N 天的专注量，按课程拆开。

    休息不计入学习时长（单独计数）—— 它反映的是节奏，不是投入。
    """
    since = now() - max(1, int(days)) * 86400
    # 本地日界。不能用 `now() - now() % 86400` —— 那是 UTC 零点，
    # 在东八区等于本地 08:00，「今天」会从早上八点开始算。
    import datetime as _dt
    today_start = _dt.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0).timestamp()
    with _conn() as c:
        t = c.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(minutes),0) AS m FROM focus_sessions"
            " WHERE kind='focus' AND at >= ?", (today_start,)
        ).fetchone()
        rows = c.execute(
            "SELECT f.course_id, COALESCE(co.code,'') AS course_code,"
            " COALESCE(co.name,'') AS course_name,"
            " COUNT(*) AS n, SUM(f.minutes) AS m"
            " FROM focus_sessions f LEFT JOIN courses co ON co.id = f.course_id"
            " WHERE f.kind='focus' AND f.at >= ?"
            " GROUP BY f.course_id ORDER BY m DESC", (since,)
        ).fetchall()
        br = c.execute(
            "SELECT COUNT(*) AS n FROM focus_sessions WHERE kind='break' AND at >= ?",
            (since,),
        ).fetchone()
    by_course = [{
        "course_id": r["course_id"] or "",
        "course_code": r["course_code"] or "",
        "course_name": r["course_name"] or "",
        "minutes": int(r["m"] or 0),
        "count": r["n"],
    } for r in rows]
    return {
        "days": max(1, int(days)),
        "today_count": t["n"],
        "today_minutes": int(t["m"] or 0),
        "week_minutes": sum(x["minutes"] for x in by_course),
        "week_by_course": by_course,
        "break_count": br["n"],
    }


# ---------- 知识图 ----------
# 一门课一张，长期维护。节点只表示「知识点」，不挂进度/正确率/页码统计
# —— 用户明确说过那些对他没意义，只有「点节点跳页码」有用。

EDGE_KINDS = {"belongs", "depends", "contrast"}
NODE_FIELDS = {"label", "material_id", "page", "parent_id", "x", "y"}


def kg_get(course_id: str) -> dict:
    with _conn() as c:
        nodes = [dict(r) for r in c.execute(
            "SELECT id, label, material_id, page, parent_id, x, y FROM kg_nodes"
            " WHERE course_id=? ORDER BY id", (course_id,))]
        edges = [dict(r) for r in c.execute(
            "SELECT id, from_id, to_id, kind FROM kg_edges WHERE course_id=? ORDER BY id",
            (course_id,))]
    return {"nodes": nodes, "edges": edges}


def kg_add_node(course_id: str, label: str = "", material_id: str = "",
                page: int = 0, parent_id: int = 0, x: float = 0, y: float = 0) -> dict:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO kg_nodes(course_id, label, material_id, page, parent_id, x, y, created_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (course_id, str(label)[:80], material_id or "", int(page or 0),
             int(parent_id or 0), float(x or 0), float(y or 0), now()),
        )
        return {"id": cur.lastrowid, "label": str(label)[:80], "material_id": material_id or "",
                "page": int(page or 0), "parent_id": int(parent_id or 0),
                "x": float(x or 0), "y": float(y or 0)}


def kg_update_node(nid: int, **fields) -> bool:
    _check_fields(fields, NODE_FIELDS, "kg_nodes")
    if not fields:
        return False
    if "label" in fields:
        fields["label"] = str(fields["label"])[:80]
    keys = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        cur = c.execute(f"UPDATE kg_nodes SET {keys} WHERE id=?", (*fields.values(), nid))
        return cur.rowcount > 0


def kg_delete_node(nid: int) -> dict:
    """删节点：子节点一起删（它们挂在这个节点下面，留着会变成孤儿），
    相关连线也一起删。"""
    removed = []
    with _conn() as c:
        row = c.execute("SELECT id, parent_id FROM kg_nodes WHERE id=?", (nid,)).fetchone()
        if not row:
            return {"deleted": 0}
        stack, ids = [nid], []
        while stack:
            cur_id = stack.pop()
            ids.append(cur_id)
            stack.extend(r["id"] for r in c.execute(
                "SELECT id FROM kg_nodes WHERE parent_id=?", (cur_id,)).fetchall())
        marks = ",".join("?" * len(ids))
        c.execute(f"DELETE FROM kg_nodes WHERE id IN ({marks})", ids)
        c.execute(f"DELETE FROM kg_edges WHERE from_id IN ({marks}) OR to_id IN ({marks})",
                  ids + ids)
        removed = ids
    return {"deleted": len(removed), "ids": removed}


def kg_add_edge(course_id: str, from_id: int, to_id: int, kind: str = "belongs") -> dict:
    kind = kind if kind in EDGE_KINDS else "belongs"
    if int(from_id) == int(to_id):
        raise ValueError("不能连到自己")
    with _conn() as c:
        # 同一对节点 + 同一类型只留一条；类型不同是允许的（既属于又依赖）
        dup = c.execute(
            "SELECT id FROM kg_edges WHERE course_id=? AND from_id=? AND to_id=? AND kind=?",
            (course_id, int(from_id), int(to_id), kind)).fetchone()
        if dup:
            return {"id": dup["id"], "duplicate": True}
        cur = c.execute(
            "INSERT INTO kg_edges(course_id, from_id, to_id, kind, created_at) VALUES(?,?,?,?,?)",
            (course_id, int(from_id), int(to_id), kind, now()),
        )
        return {"id": cur.lastrowid, "from_id": int(from_id), "to_id": int(to_id),
                "kind": kind, "duplicate": False}


def kg_delete_edge(eid: int) -> bool:
    with _conn() as c:
        return c.execute("DELETE FROM kg_edges WHERE id=?", (eid,)).rowcount > 0


def kg_has_nodes(course_id: str) -> bool:
    with _conn() as c:
        return bool(c.execute(
            "SELECT 1 FROM kg_nodes WHERE course_id=? LIMIT 1", (course_id,)).fetchone())


def kg_add_many(course_id: str, nodes: list) -> list:
    """批量插入草稿节点，并把 `parent`（草稿里的下标）换成真实 id。

    两趟：先全部插入拿到 id，再回填 parent_id。
    模型不保证父节点排在子节点前面，一趟做不到。
    """
    idmap, out = {}, []
    with _conn() as c:
        for n in nodes:
            cur = c.execute(
                "INSERT INTO kg_nodes(course_id, label, material_id, page, parent_id, x, y, created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (course_id, str(n.get("label") or "")[:80], n.get("material_id") or "",
                 int(n.get("page") or 0), 0, float(n.get("x") or 0),
                 float(n.get("y") or 0), now()),
            )
            idmap[len(out)] = cur.lastrowid
            out.append({"id": cur.lastrowid})
        for i, n in enumerate(nodes):
            p = n.get("parent", -1)
            if isinstance(p, int) and p >= 0 and p in idmap:
                c.execute("UPDATE kg_nodes SET parent_id=? WHERE id=?", (idmap[p], idmap[i]))
                out[i]["parent_id"] = idmap[p]
                # 层级关系同时落成一条「属于」连线 —— 图上所有可见的线都来自
                # kg_edges，否则父子关系画不出来（或者要额外养一套隐式边）
                c.execute(
                    "INSERT INTO kg_edges(course_id, from_id, to_id, kind, created_at)"
                    " VALUES(?,?,?,?,?)",
                    (course_id, idmap[p], idmap[i], "belongs", now()),
                )
            else:
                out[i]["parent_id"] = 0
    return out


# ---------- 速查表 ----------
# 结构固定四段：术语表 / 公式 / 代码模板 / 易错点。
# 每条挂 material_id + page，点一下跳原文；导出 PDF 时页码也印上去。

CHEAT_SECTIONS = ("terms", "formulas", "code", "pitfalls")
CHEAT_FIELDS = {"section", "title", "body", "material_id", "page", "ord"}


def cheat_list(course_id: str) -> dict:
    with _conn() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT id, section, title, body, material_id, page, ord FROM cheat_items"
            " WHERE course_id=? ORDER BY section, ord, id", (course_id,))]
        # 资料名得带上：只显示页码，用户不知道是哪份资料的第几页
        # 资料名 + ext：点条目要按 ext 选阅读器（docx 与 pdf 走的不是同一条路）
        meta = {r["id"]: (r["orig_name"], r["ext"]) for r in c.execute(
            "SELECT id, orig_name, ext FROM materials WHERE course_id=?", (course_id,)).fetchall()}
    for r in rows:
        name, ext = meta.get(r["material_id"], ("", "pdf"))
        r["orig_name"] = name
        r["ext"] = ext or "pdf"
    counts = {k: 0 for k in CHEAT_SECTIONS}
    for r in rows:
        counts[r["section"]] = counts.get(r["section"], 0) + 1
    return {"items": rows, "counts": counts}


def cheat_add_item(course_id: str, section: str, title: str, body: str,
                   material_id: str = "", page: int = 0) -> dict:
    section = section if section in CHEAT_SECTIONS else "terms"
    with _conn() as c:
        nxt = c.execute(
            "SELECT COALESCE(MAX(ord),0)+1 AS n FROM cheat_items WHERE course_id=? AND section=?",
            (course_id, section)).fetchone()["n"]
        cur = c.execute(
            "INSERT INTO cheat_items(course_id, section, title, body, material_id, page, ord, created_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (course_id, section, str(title)[:200], str(body)[:2000],
             material_id or "", int(page or 0), int(nxt), now()))
        return {"id": cur.lastrowid, "section": section, "title": str(title)[:200],
                "body": str(body)[:2000], "material_id": material_id or "",
                "page": int(page or 0), "ord": int(nxt)}


def cheat_update_item(iid: int, **fields) -> bool:
    _check_fields(fields, CHEAT_FIELDS, "cheat_items")
    if not fields:
        return False
    if "section" in fields and fields["section"] not in CHEAT_SECTIONS:
        raise ValueError("未知的段落")
    for k, lim in (("title", 200), ("body", 2000)):
        if k in fields:
            fields[k] = str(fields[k])[:lim]
    keys = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        return c.execute(f"UPDATE cheat_items SET {keys} WHERE id=?",
                         (*fields.values(), iid)).rowcount > 0


def cheat_delete_item(iid: int) -> bool:
    with _conn() as c:
        return c.execute("DELETE FROM cheat_items WHERE id=?", (iid,)).rowcount > 0


def cheat_replace(course_id: str, items: list) -> int:
    """整份替换（AI 重新生成时用）。

    旧内容一并删掉 —— 半新半旧混在一起，用户分不清哪条是刚生成的。
    前端调用前会先确认过。
    """
    with _conn() as c:
        c.execute("DELETE FROM cheat_items WHERE course_id=?", (course_id,))
        n = 0
        for sec in CHEAT_SECTIONS:
            ord_ = 0
            for it in [x for x in items if x.get("section") == sec]:
                c.execute(
                    "INSERT INTO cheat_items(course_id, section, title, body, material_id, page, ord, created_at)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                    (course_id, sec, str(it.get("title") or "")[:200],
                     str(it.get("body") or "")[:2000], it.get("material_id") or "",
                     int(it.get("page") or 0), ord_, now()))
                ord_ += 1
                n += 1
    return n


# ---------- 成绩构成 ----------

def list_assessments(course_id: str):
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, weight, score FROM assessments WHERE course_id=? ORDER BY ord",
            (course_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def replace_assessments(course_id: str, items: list[dict]):
    """items: [{name, weight, score}]，score 可为 None。"""
    with _conn() as c:
        c.execute("DELETE FROM assessments WHERE course_id=?", (course_id,))
        c.executemany(
            "INSERT INTO assessments(course_id, name, weight, score, ord) VALUES(?,?,?,?,?)",
            [
                (
                    course_id,
                    str(it.get("name") or f"Component {i + 1}"),
                    float(it.get("weight") or 0),
                    float(it["score"]) if it.get("score") is not None else None,
                    i,
                )
                for i, it in enumerate(items)
            ],
        )


def purge_material(mid: str) -> dict | None:
    """彻底删除：返回资料信息供调用方清理文件与分块。"""
    mat = get_material(mid)
    if not mat:
        return None
    with _conn() as c:
        c.execute("DELETE FROM chunks WHERE material_id=?", (mid,))
        c.execute("DELETE FROM materials WHERE id=?", (mid,))
        c.execute("DELETE FROM page_notes WHERE material_id=?", (mid,))
        c.execute("DELETE FROM material_progress WHERE material_id=?", (mid,))
        c.execute("DELETE FROM material_my_notes WHERE material_id=?", (mid,))
        c.execute("DELETE FROM page_ink WHERE material_id=?", (mid,))
        c.execute("DELETE FROM page_mynotes WHERE material_id=?", (mid,))
    return mat


# ---------- chunks / retrieval ----------

def add_chunks(course_id: str, material_id: str, chunks: list[tuple[int, int, str, bytes]]):
    """chunks: [(page, ord, text, embedding_bytes)]

    **幂等**：先清掉该资料的旧分块再插入。
    重新解析是常事（比如 Word 转出 PDF 后改成分页解析），不清旧数据就会留两套分块，
    检索时同一段内容出现两次、出处页码还互相打架。删除与插入同一连接，不会留半套。
    """
    with _conn() as c:
        c.execute("DELETE FROM chunks WHERE material_id=?", (material_id,))
        c.executemany(
            "INSERT INTO chunks(material_id, course_id, page, ord, text, embedding) VALUES(?,?,?,?,?,?)",
            [(material_id, course_id, p, o, t, e) for p, o, t, e in chunks],
        )


def material_sample_texts(material_id: str) -> list[str]:
    """取该资料「首 / 中 / 尾」三块文本，用于入库后的内容判定。

    只查 3 行，不把整本资料拉进内存（长文档可能是几 MB 文本）。
    """
    with _conn() as c:
        n = c.execute(
            "SELECT COUNT(*) AS n FROM chunks WHERE material_id=?", (material_id,)
        ).fetchone()["n"]
        if not n:
            return []
        picks, seen = [], set()
        for off in (0, n // 2, n - 1):
            if off in seen or off < 0:
                continue
            seen.add(off)
            r = c.execute(
                "SELECT text FROM chunks WHERE material_id=? ORDER BY id LIMIT 1 OFFSET ?",
                (material_id, off),
            ).fetchone()
            if r:
                picks.append(r["text"])
        return picks


def all_chunks_with_vectors(course_id: str = ""):
    """取分块与向量。course_id 为空串时跨全部课程（含未分类）——外部资料模式用。

    ord 必须带出来：检索命中一个碎片后要按 ord 把前后相邻块取回来，
    才能拼成完整段落（教材是 600 字滑窗切的，单块常从句子中间断开）。
    """
    sql = """SELECT ch.id, ch.material_id, ch.page, ch.ord, ch.text, ch.embedding,
                    m.orig_name, m.ext, co.code AS course_code
             FROM chunks ch
             JOIN materials m ON m.id = ch.material_id
             LEFT JOIN courses co ON co.id = ch.course_id
             WHERE m.deleted=0 AND ch.embedding IS NOT NULL"""
    args: list = []
    if course_id:
        sql += " AND ch.course_id=?"
        args.append(course_id)
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def chunks_by_ord_range(material_id: str, lo: int, hi: int):
    """取某资料内 ord 落在 [lo, hi] 的块，按 ord 升序。

    用途：检索命中一个碎片，把它的前后邻块一起取回拼成完整段落。
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT id, material_id, page, ord, text FROM chunks"
            " WHERE material_id=? AND ord BETWEEN ? AND ? ORDER BY ord",
            (material_id, int(lo), int(hi)),
        ).fetchall()
        return [dict(r) for r in rows]


def chunks_for_materials(material_ids: list[str]):
    """按资料 ID 取分块（用于出题），按资料 / 页 / 块序排序。

    带上 ord 是必需的：同一页的多个块要按 ord 拼回原文顺序，
    顺序错了合并出来的「知识点」就是乱的。
    """
    if not material_ids:
        return []
    marks = ",".join("?" * len(material_ids))
    with _conn() as c:
        rows = c.execute(
            f"""SELECT ch.material_id, ch.page, ch.ord, ch.text, m.orig_name, m.ext
                FROM chunks ch JOIN materials m ON m.id = ch.material_id
                WHERE ch.material_id IN ({marks}) AND m.deleted=0
                ORDER BY ch.material_id, ch.page, ch.ord""",
            material_ids,
        ).fetchall()
        return [dict(r) for r in rows]


def chunk_sizes_for_materials(material_ids: list[str]):
    """按 (资料, 页) 聚合出字数 + 页首文本。

    覆盖率分母走这条轻量查询（不把正文整段拉回来），但需要 head 判断
    「这页是不是封面/目录」—— 那类页不出题，也不能计入分母，
    否则覆盖率天花板永远到不了 100%。
    返回 [(material_id, page, chars, head), ...]
    """
    ids = [m for m in (material_ids or []) if isinstance(m, str)]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    with _conn() as c:
        rows = c.execute(
            f"""SELECT ch.material_id, ch.page,
                       COALESCE(SUM(LENGTH(ch.text)),0) AS chars,
                       COALESCE(GROUP_CONCAT(SUBSTR(ch.text,1,600),' '),'') AS head
                FROM chunks ch JOIN materials m ON m.id = ch.material_id
                WHERE ch.material_id IN ({marks}) AND m.deleted=0
                GROUP BY ch.material_id, ch.page
                ORDER BY ch.material_id, ch.page""",
            ids,
        ).fetchall()
        return [(r["material_id"], int(r["page"]), int(r["chars"]), r["head"] or "")
                for r in rows]


# ---------- messages ----------

def add_message(course_id: str, role: str, content: str, citations: list | None = None):
    with _conn() as c:
        c.execute(
            "INSERT INTO messages(course_id, role, content, citations, created_at) VALUES(?,?,?,?,?)",
            (course_id, role, content, json.dumps(citations or [], ensure_ascii=False), now()),
        )


def list_messages(course_id: str, limit: int = 200):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM messages WHERE course_id=? ORDER BY id DESC LIMIT ?",
            (course_id, limit),
        ).fetchall()
        out = [dict(r) for r in rows]
        for m in out:
            m["citations"] = json.loads(m["citations"])
        out.reverse()
        return out


def clear_messages(course_id: str):
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE course_id=?", (course_id,))


# ---------- 汇编训练 ----------

def save_asm_attempt(course_id: str, task_key: str, code: str,
                     score: int, feedback: dict) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO asm_attempts(course_id, task_key, code, score, feedback, created_at)"
            " VALUES(?,?,?,?,?,?)",
            (course_id, task_key, code, int(score),
             json.dumps(feedback or {}, ensure_ascii=False), now()),
        )
        return int(cur.lastrowid)


def asm_progress(course_id: str) -> dict:
    """每道题的最佳成绩与提交次数：{task_key: {best, tries, last_at}}"""
    with _conn() as c:
        rows = c.execute(
            "SELECT task_key, MAX(score) AS best, COUNT(*) AS tries, MAX(created_at) AS last_at"
            " FROM asm_attempts WHERE course_id=? GROUP BY task_key",
            (course_id,),
        ).fetchall()
    return {r["task_key"]: {"best": int(r["best"] or 0),
                            "tries": int(r["tries"] or 0),
                            "last_at": r["last_at"]}
            for r in rows}


def latest_asm_attempt(course_id: str, task_key: str):
    """某道题最近一次提交（含当时的代码与批改），用于「接着上次改」。"""
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM asm_attempts WHERE course_id=? AND task_key=?"
            " ORDER BY id DESC LIMIT 1",
            (course_id, task_key),
        ).fetchone()
    if not row:
        return None
    out = dict(row)
    try:
        out["feedback"] = json.loads(out.get("feedback") or "{}")
    except Exception:
        out["feedback"] = {}
    return out
