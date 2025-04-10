from flask import Flask, render_template, request, redirect, session, flash, url_for
import pymysql
import pymysql.cursors

from create_db import db_config

app = Flask(__name__)
app.secret_key = "my_secret_key"

def get_db_connection():
    return pymysql.connect(**db_config)

# 注册，*登录*，修改密码

# （当前用户）列出全部公众号并进行管理（关注或者取消关注）

# （当前用户）显示自己所关注的公众号的全部推文

# （当前用户）评论某推文或者评论

# （当前用户）点赞或者取消点赞某推文或者评论

@app.route("/")
def index():
    # 用户已登录，显示主页内容
    if 'userid' in session:
        # 获取用户主页内容，包括关注的公众号，最新推文等
        connection = get_db_connection()
        # 获取参数用于网页显示，默认显示关注的公众号
        try:
            view = request.args.get('view')
        except:
            view = 'followed'
        
        
        # 注：需要为每行查询结果添加一个 follower_cnt 字段，表示关注人数
        # 设置每一个channel的followed属性
        channels = []
        if view == 'followed':
            # 将关注的公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, 1 AS followed
                    FROM followed_channels AS fc
                    JOIN channels AS c ON fc.nid = c.nid
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """, (session['userid']))
                channels = cursor.fetchall()
        elif view == 'all':
            # 将全部公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, CASE WHEN c.nid IN (SELECT nid FROM followed_channels) THEN 1 ELSE 0 END AS followed
                    FROM channels AS c
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """, (session['userid']))
                channels = cursor.fetchall()
        elif view == 'managed':
            # 将用户管理的公众号的数据存入 channels 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    WITH followed_channels AS (SELECT s.nid FROM subscribe AS s WHERE s.uid = %s),
                    managed_channels AS (SELECT s.nid FROM manage_channel AS s WHERE s.uid = %s),
                    channel_follower_cnt AS (SELECT s.nid, COUNT(s.uid) AS count FROM subscribe AS s GROUP BY s.nid)
                    SELECT c.nid, c.name, u.username AS created_by, cn.count AS follower_cnt, CASE WHEN c.nid IN (SELECT nid FROM followed_channels) THEN 1 ELSE 0 END AS followed
                    FROM managed_channels AS mc
                    JOIN channels AS c ON mc.nid = c.nid
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """, (session['userid'], session['userid']))
                channels = cursor.fetchall()

        # 获取参数用于选择公众号
        selected_channel_name = request.args.get('selected_channel_name')
        selected_channel_id = request.args.get('selected_channel_id')
        
        # 注：需要为每行查询结果添加一个 like_cnt 字段，表示点赞数量
        posts = []
        if selected_channel_name is not None:
            # TODO: 将选择的公众号的最新推文存入 posts 中
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    WITH 
                    SELECT p.title, p.created_at,  AS like_cnt
                    FROM managed_channels AS mc
                    JOIN channels AS c ON mc.nid = c.nid
                    JOIN users AS u ON u.uid = c.created_by
                    JOIN channel_follower_cnt AS cn ON cn.nid = c.nid;
                """, ())
                posts = cursor.fetchall()
        elif view == 'followed':
            # TODO: 将关注的公众号的最新推文存入 posts 中
            posts = []
        elif view == 'all':
            # TODO: 将全部公众号的最新推文存入 posts 中
            posts = []
        elif view == 'managed':
            # TODO: 将用户管理的公众号的最新推文存入 posts 中
            posts = []

            
        connection.close()
        # TODO: index 渲染需要三个数据：用户信息，中侧栏所需公众号信息，右侧栏所需推文信息
        return render_template("index.html", 
            user={'name': session['username']},
            channels=channels,
            posts=[],
            view_type=view,
            selected_channel_name=selected_channel_name
            )
    else:
    # 用户未登录，重定向到登录页面
        return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # TODO: 验证用户名和密码
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.uid, u.password
                FROM users AS u
                WHERE u.username = %s
            """, (username))
            result = cursor.fetchone()
            if result and result[1] == password:
                # 如果验证成功，将用户信息存储在session中
                session['userid'] = result[0]
                session['username'] = username
                return redirect(url_for('index'))
        connection.close()
        flash("Invalid username or password", "danger")
    
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # TODO: 注册新用户，是否需要检测注册是否成功？
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, password)
                    VALUES (%s, %s);
                """, (username, password))
            connection.commit()
            # 如果注册成功，重定向到登录页面
            flash("Register success, please login", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"username '{username}' is occupied, please use another username", "danger")
            return render_template("register.html")
        finally:
            connection.close()
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop('userid', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route("/follow/<channel_id>")
def follow(channel_id):
    if 'userid' in session:
        # TODO: 关注公众号
        
        flash("Followed channel {555}", 'info')
        return redirect(url_for('index', view=request.args.get('view'), selected_channel=request.args.get('selected_channel')))
    else:
        return redirect(url_for('login'))
    

@app.route("/unfollow/<channel_id>")
def unfollow(channel_id):
    if 'userid' in session:
        # TODO: 取消关注公众号

        flash("Unfollowed channel {555}", 'info')
        return redirect(url_for('index', view=request.args.get('view'), selected_channel=request.args.get('selected_channel')))
    else:
        return redirect(url_for('login'))


@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    if 'userid' in session:
        # TODO: 删除推文，可能需要检测权限
        flash("Deleted post {555}", 'info')
        return redirect(url_for('index', view=request.args.get('view'), selected_channel=request.args.get('selected_channel')))
    else:
        return redirect(url_for('login'))


@app.route("/post/<pid>")
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
