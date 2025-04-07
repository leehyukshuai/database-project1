# create_db.py
import pymysql


def create_db():
    # 创建数据库连接
    db_config = {
        "host": "10.129.195.217",
        "user": "hs",
        "password": "",
        "database": "db_hs",
        "charset": "utf8mb4",
    }
    connection = pymysql.connect(**db_config)

    try:
        with connection.cursor() as cursor:
            # clear database
            cursor.execute(
                """
            DROP TABLE IF EXISTS like_comment, like_post, belong_to_theme, interested_in_theme, manage_channel, subscribe, themes, comments, posts, channels, users;
            """
            )

            # create tables
            cursor.execute(
                """
            CREATE TABLE users (
                uid INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(300) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE channels (
                nid INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(uid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE posts (
                pid INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(50) UNIQUE NOT NULL,
                from_channel INT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_channel) REFERENCES channels(nid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE comments (
                cid INT,
                pid INT,
                from_user INT,
                to_comment INT,
                master_comment INT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pid) REFERENCES posts(pid),
                FOREIGN KEY (from_user) REFERENCES users(uid),
                FOREIGN KEY (to_comment, pid) REFERENCES comments(cid, pid),
                FOREIGN KEY (master_comment, pid) REFERENCES comments(cid, pid),
                PRIMARY KEY (cid, pid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE themes (
                tid INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE subscribe (
                uid INT NOT NULL,
                nid INT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid),
                FOREIGN KEY (nid) REFERENCES channels(nid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE manage_channel (
                uid INT NOT NULL,
                nid INT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid),
                FOREIGN KEY (nid) REFERENCES channels(nid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE like_post (
                uid INT NOT NULL,
                pid INT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid),
                FOREIGN KEY (pid) REFERENCES posts(pid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE like_comment (
                uid INT NOT NULL,
                cid INT NOT NULL,
                pid INT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid),
                FOREIGN KEY (cid, pid) REFERENCES comments(cid, pid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE interested_in_theme (
                uid INT NOT NULL,
                tid INT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid),
                FOREIGN KEY (tid) REFERENCES themes(tid)
            );
            """
            )

            cursor.execute(
                """
            CREATE TABLE belong_to_theme (
                pid INT NOT NULL,
                tid INT NOT NULL,
                FOREIGN KEY (pid) REFERENCES posts(pid),
                FOREIGN KEY (tid) REFERENCES themes(tid)
            );
            """
            )

            # insert values
            cursor.execute(
                """
            -- 插入用户数据
            INSERT INTO users (username, password) VALUES 
            ('alice', 'alice123'),
            ('bob', 'bob123'),
            ('charlie', 'charlie123'),
            ('david', 'david123'),
            ('eve', 'eve123');
            """
            )

            cursor.execute(
                """
            -- 插入公众号数据
            INSERT INTO channels (name, created_by) VALUES 
            ('TechNews', 1),
            ('GadgetReviews', 2),
            ('ScienceDaily', 3),
            ('HealthTips', 4),
            ('TravelBlog', 5);
            """
            )

            cursor.execute(
                """
            -- 插入主题数据
            INSERT INTO themes (type, description) VALUES 
            ('Technology', 'All about technology and innovation'),
            ('Science', 'Discoveries and scientific research'),
            ('Health', 'Health tips and wellness'),
            ('Travel', 'Travel destinations and experiences'),
            ('Gadgets', 'Latest gadgets and reviews');
            """
            )

            cursor.execute(
                """
            -- 插入用户关注的公众号关系
            INSERT INTO subscribe (uid, nid) VALUES 
            (1, 1), (1, 2), (1, 3),  -- Alice关注TechNews, GadgetReviews, ScienceDaily
            (2, 1), (2, 4),          -- Bob关注TechNews, HealthTips
            (3, 2), (3, 5),          -- Charlie关注GadgetReviews, TravelBlog
            (4, 3), (4, 4), (4, 5),  -- David关注ScienceDaily, HealthTips, TravelBlog
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5); -- Eve关注所有公众号
            """
            )

            cursor.execute(
                """
            -- 插入用户管理的公众号关系
            INSERT INTO manage_channel (uid, nid) VALUES 
            (1, 1),  -- Alice管理TechNews
            (2, 2),  -- Bob管理GadgetReviews
            (3, 3),  -- Charlie管理ScienceDaily
            (4, 4),  -- David管理HealthTips
            (5, 5);  -- Eve管理TravelBlog
            """
            )

            cursor.execute(
                """
            -- 插入推文数据（每个公众号多篇推文）
            INSERT INTO posts (title, from_channel, content) VALUES 
            ('AI Breakthroughs', 1, 'Latest advancements in AI technology'),
            ('Smartphone Comparison', 2, 'Comparing the latest smartphones'),
            ('Quantum Computing', 1, 'Understanding quantum computing basics'),
            ('Wearable Tech', 2, 'Review of the newest wearable devices'),
            ('Space Exploration', 3, 'Recent developments in space research'),
            ('Nutrition Tips', 4, 'Healthy eating habits for better wellness'),
            ('Travel Destinations', 5, 'Top travel destinations for 2023'),
            ('Mental Health', 4, 'Tips for maintaining mental health'),
            ('Vacation Planning', 5, 'How to plan the perfect vacation'),
            ('Future of Work', 1, 'How technology is reshaping workplaces');
            """
            )

            cursor.execute(
                """
            -- 插入推文所属的主题关系
            INSERT INTO belong_to_theme (pid, tid) VALUES 
            (1, 1), (1, 5),  -- AI Breakthroughs属于Technology和Gadgets
            (2, 5),          -- Smartphone Comparison属于Gadgets
            (3, 1),          -- Quantum Computing属于Technology
            (4, 5),          -- Wearable Tech属于Gadgets
            (5, 2),          -- Space Exploration属于Science
            (6, 3),          -- Nutrition Tips属于Health
            (7, 4),          -- Travel Destinations属于Travel
            (8, 3),          -- Mental Health属于Health
            (9, 4),          -- Vacation Planning属于Travel
            (10, 1);         -- Future of Work属于Technology

            -- 插入评论数据（复杂结构）"""
            )

            cursor.execute(
                """
            -- 对于推文1的评论
            INSERT INTO comments (cid, pid, from_user, to_comment, master_comment, content) VALUES 
            (0, 1, 2, NULL, NULL, 'Great insights on AI!'),  -- 根评论
            (1, 1, 3, 0, 0, 'I agree, especially about neural networks.'),  -- 回复根评论
            (2, 1, 5, 0, 0, 'What about ethical considerations?'),  -- 回复根评论
            (3, 1, 1, 1, 0, 'Thanks! I think ethics is crucial too.'),  -- 回复评论1
            (4, 1, 4, 2, 0, 'That''s a good point. We need more discussion on AI ethics.');  -- 回复评论2
            """
            )

            cursor.execute(
                """
            -- 对于推文2的评论
            INSERT INTO comments (cid, pid, from_user, to_comment, master_comment, content) VALUES 
            (0, 2, 1, NULL, NULL, 'Which smartphone do you recommend?'),  -- 根评论
            (1, 2, 3, 0, 0, 'I prefer the newer model for battery life.'),  -- 回复根评论
            (2, 2, 5, 0, 0, 'Price is also a factor for me.'),  -- 回复根评论
            (3, 2, 2, 1, 0, 'Battery life is important, but so is camera quality.'),  -- 回复评论1
            (4, 2, 4, 2, 0, 'Agreed. Value for money is key.');  -- 回复评论2
            """
            )

            cursor.execute(
                """
            -- 对于推文5的评论
            INSERT INTO comments (cid, pid, from_user, to_comment, master_comment, content) VALUES 
            (0, 5, 4, NULL, NULL, 'Fascinating developments in space!'),  -- 根评论
            (1, 5, 5, 0, 0, 'I hope we see more missions soon.'),  -- 回复根评论
            (2, 5, 2, 0, 0, 'What about Mars colonization?'),  -- 回复根评论
            (3, 5, 3, 1, 0, 'Me too! Space exploration inspires innovation.'),  -- 回复评论1
            (4, 5, 1, 2, 0, 'That''s the next big frontier. Very exciting!');  -- 回复评论2
            """
            )

            cursor.execute(
                """
            -- 插入用户点赞推文的关系
            INSERT INTO like_post (uid, pid) VALUES 
            (1, 1), (1, 3), (1, 5), (1, 7),  -- Alice点赞
            (2, 2), (2, 4), (2, 6),          -- Bob点赞
            (3, 1), (3, 2), (3, 9),          -- Charlie点赞
            (4, 5), (4, 6), (4, 8),          -- David点赞
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10);  -- Eve点赞所有推文
            """
            )

            cursor.execute(
                """
            -- 插入用户点赞评论的关系
            INSERT INTO like_comment (uid, cid, pid) VALUES 
            (1, 0, 1), (1, 3, 1),  -- Alice点赞推文1的评论0和3
            (2, 1, 2), (2, 4, 2),  -- Bob点赞推文2的评论1和4
            (3, 0, 5), (3, 2, 5),  -- Charlie点赞推文5的评论0和2
            (4, 4, 5),             -- David点赞推文5的评论4
            (5, 0, 1), (5, 1, 1), (5, 2, 1), (5, 3, 1), (5, 4, 1),  -- Eve点赞推文1的所有评论
            (5, 0, 2), (5, 1, 2), (5, 2, 2), (5, 3, 2), (5, 4, 2),  -- Eve点赞推文2的所有评论
            (5, 0, 5), (5, 1, 5), (5, 2, 5), (5, 3, 5), (5, 4, 5);  -- Eve点赞推文5的所有评论
            """
            )

            cursor.execute(
                """
            -- 插入用户感兴趣的主题关系
            INSERT INTO interested_in_theme (uid, tid) VALUES 
            (1, 1), (1, 2), (1, 5),  -- Alice对Technology, Science, Gadgets感兴趣
            (2, 5), (2, 3),          -- Bob对Gadgets, Health感兴趣
            (3, 4), (3, 5),          -- Charlie对Travel, Gadgets感兴趣
            (4, 2), (4, 3), (4, 4),  -- David对Science, Health, Travel感兴趣
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5);  -- Eve对所有主题感兴趣
            """
            )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    create_db()
