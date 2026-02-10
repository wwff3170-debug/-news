from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

APP_SECRET = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ADMIN_PASSWORD = "nationnews"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "newspapers.db")

app = Flask(__name__)
app.secret_key = APP_SECRET


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newspapers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    """)
    conn.commit()

    # 如果数据库为空，插入一些示例
    cur.execute("SELECT COUNT(*) AS c FROM newspapers")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO newspapers (name, url) VALUES (?, ?)",
            [
                ("人民日报", "https://www.people.com.cn/"),
                ("新华社", "https://www.xinhuanet.com/"),
                ("光明日报", "https://www.gmw.cn/"),
            ],
        )
        conn.commit()
    conn.close()


# 初始化数据库
with app.app_context():
    init_db()


@app.route("/")
def index():
    conn = get_db()
    papers = conn.execute("SELECT * FROM newspapers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", papers=papers)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("is_admin"):
        if request.method == "POST":
            pwd = request.form.get("password", "")
            if pwd == ADMIN_PASSWORD:
                session["is_admin"] = True
                return redirect(url_for("admin_panel"))
            flash("密码错误，请重试。")
        return render_template("admin_login.html")
    return redirect(url_for("admin_panel"))


@app.route("/admin/panel")
def admin_panel():
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    papers = conn.execute("SELECT * FROM newspapers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_panel.html", papers=papers)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


@app.route("/admin/add", methods=["POST"])
def admin_add():
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    if not name or not url:
        flash("报刊名称和网址都不能为空。")
        return redirect(url_for("admin_panel"))
    conn = get_db()
    conn.execute("INSERT INTO newspapers (name, url) VALUES (?, ?)", (name, url))
    conn.commit()
    conn.close()
    flash("新增成功。")
    return redirect(url_for("admin_panel"))


@app.route("/admin/edit/<int:paper_id>", methods=["POST"])
def admin_edit(paper_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    if not name or not url:
        flash("报刊名称和网址都不能为空。")
        return redirect(url_for("admin_panel"))
    conn = get_db()
    conn.execute("UPDATE newspapers SET name=?, url=? WHERE id=?", (name, url, paper_id))
    conn.commit()
    conn.close()
    flash("编辑成功。")
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete/<int:paper_id>", methods=["POST"])
def admin_delete(paper_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("DELETE FROM newspapers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()
    flash("删除成功。")
    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
