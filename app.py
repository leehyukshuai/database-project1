from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for,
    jsonify,
)
import pymysql
import pymysql.cursors

from create_db import db_config

app = Flask(__name__)
app.secret_key = "my_secret_key"


def get_db_connection():
    return pymysql.connect(**db_config)


# TODO: 添加修改密码的逻辑


@app.route("/")
def index():
    # 用户已登录，显示主页内容
    if "userid" in session:
        # 获取用户主页内容，包括关注的公众号，最新推文等
        connection = get_db_connection()
        # 获取参数用于网页显示，默认显示关注的公众号
        view = request.args.get("view", "all")

        # 注：需要为每行查询结果添加一个 follower_cnt 字段，表示关注人数
        # 设置每一个channel的followed属性
        channels = []
        if view == "followed":
            # 将关注的公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, 1 AS followed
                    FROM followed_channels AS fc
                    JOIN channels AS c ON fc.nid = c.nid
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """,
                    (session["userid"]),
                )
                channels = cursor.fetchall()
        elif view == "all":
            # 将全部公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, CASE WHEN c.nid IN (SELECT nid FROM followed_channels) THEN 1 ELSE 0 END AS followed
                    FROM channels AS c
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """,
                    (session["userid"]),
                )
                channels = cursor.fetchall()
        elif view == "managed":
            # 将用户管理的公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    managed_channels AS (SELECT s.nid FROM manage_channel AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, CASE WHEN c.nid IN (SELECT nid FROM followed_channels) THEN 1 ELSE 0 END AS followed
                    FROM managed_channels AS mc
                    JOIN channels AS c ON mc.nid = c.nid
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """,
                    (session["userid"], session["userid"]),
                )
                channels = cursor.fetchall()

        # 获取参数用于选择公众号
        selected_channel_name = request.args.get("selected_channel_name")
        selected_channel_id = request.args.get("selected_channel_id")

        # 注：需要为每行查询结果添加一个 like_cnt 字段，表示点赞数量
        posts = []
        if selected_channel_name is not None:
            # 将选择的公众号的最新推文存入 posts 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH post_liker_cnt AS (SELECT lp.pid, COUNT(lp.uid) AS count FROM like_post AS lp GROUP BY lp.pid)
                    SELECT p.pid, p.title, p.created_at, lc.count AS like_cnt
                    FROM posts AS p
                    JOIN post_liker_cnt AS lc ON p.pid = lc.pid
                    WHERE p.from_channel = %s;
                """,
                    (selected_channel_id),
                )
                posts = cursor.fetchall()
        elif view == "followed":
            # 将关注的公众号的最新推文存入 posts 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH post_liker_cnt AS (SELECT lp.pid, COUNT(lp.uid) AS count FROM like_post AS lp GROUP BY lp.pid),
                    followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s)
                    SELECT p.pid, p.title, p.created_at, lc.count AS like_cnt
                    FROM posts AS p
                    JOIN post_liker_cnt AS lc ON p.pid = lc.pid
                    WHERE p.from_channel IN (SELECT * FROM followed_channels);
                """,
                    (session["userid"]),
                )
                posts = cursor.fetchall()
        elif view == "all":
            # 将全部公众号的最新推文存入 posts 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH post_liker_cnt AS (SELECT lp.pid, COUNT(lp.uid) AS count FROM like_post AS lp GROUP BY lp.pid)
                    SELECT p.pid, p.title, p.created_at, lc.count AS like_cnt
                    FROM posts AS p
                    JOIN post_liker_cnt AS lc ON p.pid = lc.pid;
                """
                )
                posts = cursor.fetchall()
        elif view == "managed":
            # 将用户管理的公众号的最新推文存入 posts 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    WITH post_liker_cnt AS (SELECT lp.pid, COUNT(lp.uid) AS count FROM like_post AS lp GROUP BY lp.pid),
                    managed_channels AS (SELECT s.nid FROM manage_channel AS s WHERE s.uid = %s)
                    SELECT p.pid, p.title, p.created_at, lc.count AS like_cnt
                    FROM posts AS p
                    JOIN post_liker_cnt AS lc ON p.pid = lc.pid
                    WHERE p.from_channel IN (SELECT * FROM managed_channels);
                """,
                    (session["userid"]),
                )
                posts = cursor.fetchall()

        connection.close()
        # index 渲染需要三个数据：用户信息，中侧栏所需公众号信息，右侧栏所需推文信息
        return render_template(
            "index.html",
            user={"name": session["username"]},
            channels=channels,
            posts=posts,
            view_type=view,
            selected_channel={"name": selected_channel_name, "id": selected_channel_id},
        )
    else:
        # 用户未登录，重定向到登录页面
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 验证用户名和密码
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.uid, u.password
                FROM users AS u
                WHERE u.username = %s
            """,
                (username),
            )
            result = cursor.fetchone()
            if result and result[1] == password:
                # 如果验证成功，将用户信息存储在session中
                session["userid"] = result[0]
                session["username"] = username
                return redirect(url_for("index"))
        connection.close()
        flash("Invalid username or password", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 注册新用户，是否需要检测注册是否成功？
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, password)
                    VALUES (%s, %s);
                """,
                    (username, password),
                )
            # # autocommit已经被启用，无需手动commit
            # connection.commit()
            # 如果注册成功，重定向到登录页面
            flash("Register success, please login", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(
                f"username '{username}' is occupied, please use another username",
                "danger",
            )
            return render_template("register.html")
        finally:
            connection.close()
    return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "userid" not in session:
        flash("请先登录", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # 验证表单数据
        if not all([old_password, new_password, confirm_password]):
            flash("请填写所有字段", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("新密码与确认密码不一致", "danger")
            return redirect(url_for("change_password"))

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 验证旧密码
                cursor.execute(
                    "SELECT password FROM users WHERE uid = %s", (session["userid"],)
                )
                result = cursor.fetchone()

                if not result or result[0] != old_password:
                    flash("旧密码不正确", "danger")
                    return redirect(url_for("change_password"))

                # 更新密码
                cursor.execute(
                    "UPDATE users SET password = %s WHERE uid = %s",
                    (new_password, session["userid"]),
                )
                connection.commit()
                flash("密码修改成功，请重新登录", "success")
                session.clear()
                return redirect(url_for("login"))
        except Exception as e:
            flash("密码修改失败，请稍后再试", "danger")
            return redirect(url_for("change_password"))
        finally:
            connection.close()

    return render_template("change_password.html")


@app.route("/logout")
def logout():
    session.pop("userid", None)
    session.pop("username", None)
    return redirect(url_for("index"))


@app.route("/follow")
def follow():
    if "userid" in session:
        # 关注公众号
        channel_id = request.args.get("channel_id")
        channel_name = request.args.get("channel_name")
        # 以下三个参数是为了保持页面一致性
        selected_channel_name = request.args.get("selected_channel_name")
        selected_channel_id = request.args.get("selected_channel_id")
        view = request.args.get("view")
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO subscribe (uid, nid)
                    VALUES(%s,%s)
                """,
                    (session["userid"], channel_id),
                )
            connection.commit()
            # 如果关注成功，重定向到主页
            flash(f"‘{session['username']}' followed channel {channel_name}", "info")
            return redirect(
                url_for(
                    "index",
                    view=view,
                    selected_channel={
                        "name": selected_channel_name,
                        "id": selected_channel_id,
                    },
                )
            )
        except Exception as e:
            # 否则告知用户无法关注该公众号（已经关注）
            flash(
                f"'{session['username']}' has already followed channel {channel_name}",
                "danger",
            )
            return redirect(
                url_for(
                    "index",
                    view=view,
                    selected_channel={
                        "name": selected_channel_name,
                        "id": selected_channel_id,
                    },
                )
            )
        finally:
            connection.close()
    else:
        return redirect(url_for("login"))


@app.route("/unfollow")
def unfollow():
    if "userid" in session:
        # 取消关注公众号
        channel_id = request.args.get("channel_id")
        channel_name = request.args.get("channel_name")
        # 以下三个参数是为了保持页面一致性
        selected_channel_name = request.args.get("selected_channel_name")
        selected_channel_id = request.args.get("selected_channel_id")
        view = request.args.get("view")
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM subscribe AS s
                    WHERE s.uid = %s and s.nid = %s;
                """,
                    (session["userid"], channel_id),
                )
            connection.commit()
            # 如果取消关注成功，重定向到主页
            flash(f"‘{session['username']}' unfollowed channel {channel_name}", "info")
            return redirect(
                url_for(
                    "index",
                    view=view,
                    selected_channel={
                        "name": selected_channel_name,
                        "id": selected_channel_id,
                    },
                )
            )
        except Exception as e:
            # 否则告知用户无法取消关注该公众号（尚未关注）
            flash(
                f"'{session['username']}' hasn't followed channel {channel_name}",
                "danger",
            )
            return redirect(
                url_for(
                    "index",
                    view=view,
                    selected_channel={
                        "name": selected_channel_name,
                        "id": selected_channel_id,
                    },
                )
            )
        finally:
            connection.close()
    else:
        return redirect(url_for("login"))


@app.route("/delete_post")
def delete_post():
    if "userid" in session:
        # 删除推文，需要检测权限
        user_id = session["userid"]
        user_name = session["username"]
        post_id = request.args.get("post_id")
        post_name = request.args.get("post_name")
        ret = redirect(
            url_for(
                "index",
                view=request.args.get("view"),
                selected_channel={
                    "name": request.args.get("selected_channel_name"),
                    "id": request.args.get("selected_channel_id"),
                },
            )
        )
        # try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # 查找post_id所属于的channel
                cursor.execute(
                    """
                    SELECT p.from_channel FROM posts AS p
                    WHERE p.pid = %s;
                """,
                    (post_id),
                )
                result = cursor.fetchone()
                # 如果删除的pid不存在
                if result is None:
                    flash(f"#{post_id}:'{post_name}' doesn't exist", "danger")
                    return ret
                # 检查权限：在manage_channels中有uid=session['userid'],nid=belonged_channel的条目
                belonged_channel = result[0]
                cursor.execute(
                    """
                    SELECT *
                    FROM manage_channel as mc
                    WHERE mc.uid = %s and mc.nid = %s;
                """,
                    (user_id, belonged_channel),
                )
                result = cursor.fetchone()
                if result is None:
                    flash(
                        f"'{user_name}' doesn't has permission to delete #{post_id}:'{post_name}'",
                        "danger",
                    )
                    return ret
                # 删除推文前，删除所有依赖这篇推文的内容
                # 按照次序：like_comment, like_post, comments, belong_to_theme, posts
                cursor.execute(
                    """
                    DELETE FROM like_comment AS lc
                    WHERE lc.pid = %s;
                """,
                    (post_id),
                )
                cursor.execute(
                    """
                    DELETE FROM like_post AS lp
                    WHERE lp.pid = %s;
                """,
                    (post_id),
                )
                cursor.execute(
                    """
                    DELETE FROM comments AS c
                    WHERE c.pid = %s;
                """,
                    (post_id),
                )
                cursor.execute(
                    """
                    DELETE FROM belong_to_theme AS bt
                    WHERE bt.pid = %s;
                """,
                    (post_id),
                )
                cursor.execute(
                    """
                    DELETE FROM posts AS p
                    WHERE p.pid = %s;
                """,
                    (post_id),
                )
            connection.commit()
            # 如果删除推文成功，重定向到主页
            flash(f"‘{session['username']}' deleted #{post_id}:'{post_name}'", "info")
            return ret
    else:
        return redirect(url_for("login"))


@app.route("/show_post/<post_id>")
def show_post(post_id):
    with get_db_connection() as conn:
        with conn.cursor(
            pymysql.cursors.DictCursor
        ) as dictcursor, conn.cursor() as cursor:
            # 获取文章信息（添加总评论数）
            dictcursor.execute(
                """
                SELECT p.*, c.name AS channel_name, 
                (SELECT COUNT(*) FROM comments WHERE pid = p.pid) AS comment_count
                FROM posts AS p 
                JOIN channels c ON p.from_channel = c.nid 
                WHERE p.pid = %s
            """,
                (post_id),
            )
            post = dictcursor.fetchone()
            if post is None:
                return redirect(url_for("index"))

            # 获取点赞用户列表
            cursor.execute(
                """
                SELECT u.username 
                FROM like_post lp
                JOIN users u ON lp.uid = u.uid
                WHERE lp.pid = %s
            """,
                (post_id,),
            )
            likers = [i[0] for i in cursor.fetchall()]
            if "username" in session:
                user_name = session["username"]
                post["liked"] = user_name in likers

            post["liker_count"] = len(likers)

            # 结构化查询评论
            def get_comments(parent_comment_id=None):
                base_query = """
                    SELECT c.cid, u.username, c.content, c.master_comment,
                    ru.username AS reply_to_user, rc.content AS reply_to_content
                    FROM comments c
                    LEFT JOIN users u ON c.from_user = u.uid
                    LEFT JOIN comments rc ON c.to_comment = rc.cid AND c.pid = rc.pid
                    LEFT JOIN users ru ON rc.from_user = ru.uid
                    WHERE c.pid = %s
                """
                params = [post_id]

                if parent_comment_id is None:
                    base_query += " AND c.master_comment IS NULL"
                else:
                    base_query += " AND c.master_comment = %s"
                    params.append(parent_comment_id)

                base_query += " ORDER BY c.created_at DESC;"

                dictcursor.execute(base_query, tuple(params))

                comments = []
                for comment in dictcursor.fetchall():
                    comment["likers"] = get_comment_likers(comment["cid"])
                    if "username" in session:
                        user_name = session["username"]
                        comment["liked"] = user_name in comment["likers"]
                    if parent_comment_id is None:
                        comment["replies"] = get_comments(comment["cid"])
                    comments.append(comment)
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
                    (cid, post_id),
                )
                return [row[0] for row in cursor.fetchall()]

            comments_tree = get_comments()

    return render_template(
        "post.html",
        post=post,
        comments=comments_tree,
        likers=likers,
    )


@app.route("/like_post", methods=["POST"])
def like_post():
    if "userid" not in session:
        return jsonify({"success": False, "message": "请先登录"})

    post_id = request.form.get("post_id")
    user_id = session["userid"]

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM like_post
                WHERE uid = %s AND pid = %s
                """,
                (user_id, post_id),
            )
            result = cursor.fetchone()

            if result:
                # 如果已经点赞，取消点赞
                cursor.execute(
                    """
                    DELETE FROM like_post
                    WHERE uid = %s AND pid = %s
                    """,
                    (user_id, post_id),
                )
                connection.commit()
                return jsonify(
                    {"success": True, "message": "取消点赞成功", "liked": False}
                )
            else:
                # 如果未点赞，添加点赞
                cursor.execute(
                    """
                    INSERT INTO like_post (uid, pid)
                    VALUES (%s, %s)
                    """,
                    (user_id, post_id),
                )
                connection.commit()
                return jsonify({"success": True, "message": "点赞成功", "liked": True})
    except Exception as e:
        return jsonify({"success": False, "message": "操作失败"})
    finally:
        connection.close()


@app.route("/like_comment", methods=["POST"])
def like_comment():
    if "userid" not in session:
        return jsonify({"success": False, "message": "请先登录"})

    comment_id = request.form.get("comment_id")
    post_id = request.form.get("post_id")
    user_id = session["userid"]

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM like_comment
                WHERE uid = %s AND pid = %s AND cid = %s
                """,
                (user_id, post_id, comment_id),
            )
            result = cursor.fetchone()

            if result:
                # 如果已经点赞，取消点赞
                cursor.execute(
                    """
                    DELETE FROM like_comment
                    WHERE uid = %s AND pid = %s AND cid = %s
                    """,
                    (user_id, post_id, comment_id),
                )
                connection.commit()
                return jsonify(
                    {"success": True, "message": "取消点赞成功", "liked": False}
                )
            else:
                # 如果未点赞，添加点赞
                cursor.execute(
                    """
                    INSERT INTO like_comment (uid, pid, cid)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, post_id, comment_id),
                )
                connection.commit()
                return jsonify({"success": True, "message": "点赞成功", "liked": True})
    except Exception as e:
        return jsonify({"success": False, "message": "操作失败"})
    finally:
        connection.close()


@app.route("/add_comment", methods=["POST"])
def add_comment():
    if "userid" not in session:
        return jsonify({"success": False, "message": "请先登录"})

    post_id = request.form.get("post_id")
    user_id = session["userid"]
    content = request.form.get("content")
    master_comment_id = request.form.get("master_comment_id")
    to_comment_id = request.form.get("to_comment_id")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (%s, %s, %s, %s, %s);
                """,
                (post_id, user_id, to_comment_id, master_comment_id, content),
            )
        connection.commit()
        return jsonify({"success": True, "message": "评论成功"})
    except Exception as e:
        return jsonify({"success": False, "message": "评论失败"})
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)
