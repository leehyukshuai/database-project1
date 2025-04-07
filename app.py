from flask import Flask, render_template, request, redirect
import pymysql

app = Flask(__name__)

# 数据库配置
db_config = {
    "host": "10.129.195.217",
    "user": "hs",
    "password": "",
    "database": "db_hs",
    "charset": "utf8mb4",
}


def get_db_connection():
    return pymysql.connect(**db_config)


@app.route("/")
def index():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 修改后的查询（添加JOIN获取频道名称）
            cursor.execute(
                """
                SELECT p.*, c.name AS channel_name
                FROM posts p
                JOIN channels c ON p.from_channel = c.nid
                ORDER BY created_at DESC
                LIMIT 5
            """
            )
            posts = [
                dict(
                    zip(
                        [
                            "pid",
                            "title",
                            "from_channel",
                            "content",
                            "created_at",
                            "channel_name",
                        ],
                        post,
                    )
                )
                for post in cursor.fetchall()
            ]
        return render_template("index.html", posts=posts)
    finally:
        conn.close()


@app.route("/post/<int:pid>")
def show_post(pid):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 获取文章信息（添加总评论数）
            cursor.execute(
                """
                SELECT p.*, c.name, 
                (SELECT COUNT(*) FROM comments WHERE pid = p.pid) AS comment_count
                FROM posts p 
                JOIN channels c ON p.from_channel = c.nid 
                WHERE p.pid = %s
            """,
                (pid,),
            )
            post = cursor.fetchone()

            # 获取点赞用户列表
            cursor.execute(
                """
                SELECT u.username 
                FROM like_post lp
                JOIN users u ON lp.uid = u.uid
                WHERE lp.pid = %s
            """,
                (pid,),
            )
            likers = [row[0] for row in cursor.fetchall()]

            # 修正后的评论查询
            def get_comments(parent_id=None):
                base_query = """
                    SELECT c.*, u.username, 
                    ru.username AS reply_to_user, rc.content AS reply_to_content
                    FROM comments c
                    LEFT JOIN users u ON c.from_user = u.uid
                    LEFT JOIN comments rc ON c.to_comment = rc.cid AND c.pid = rc.pid
                    LEFT JOIN users ru ON rc.from_user = ru.uid
                    WHERE c.pid = %s
                """
                params = [pid]

                if parent_id is None:
                    base_query += " AND c.master_comment IS NULL"
                else:
                    base_query += " AND c.master_comment = %s"
                    params.append(parent_id)

                cursor.execute(base_query, tuple(params))

                comments = []
                for comment in cursor.fetchall():
                    comment_dict = {
                        "cid": comment[0],
                        "username": comment[7],
                        "content": comment[5],
                        "reply_to": (
                            {"user": comment[8], "content": comment[9]}
                            if comment[8]
                            else None
                        ),
                        "replies": get_comments(comment[0]),
                        "likers": get_comment_likers(comment[0]),
                    }
                    comments.append(comment_dict)
                return comments

            # 获取评论点赞者
            def get_comment_likers(cid):
                cursor.execute(
                    """
                    SELECT u.username 
                    FROM like_comment lc
                    JOIN users u ON lc.uid = u.uid
                    WHERE lc.cid = %s AND lc.pid = %s
                """,
                    (cid, pid),
                )
                return [row[0] for row in cursor.fetchall()]

            comments_tree = get_comments()

        return render_template(
            "post.html",
            post=dict(
                zip(
                    [
                        "pid",
                        "title",
                        "from_channel",
                        "content",
                        "created_at",
                        "channel_name",
                        "comment_count",
                    ],
                    post,
                )
            ),
            comments=comments_tree,
            likers=likers,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
