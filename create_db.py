# create_db.py
import pymysql

db_config = {
    "host": "10.129.195.217",
    "user": "hw1",
    "password": "",
    "database": "db_hw1",
    "charset": "utf8mb4",
    "autocommit": True,
}


def create_db():
    # 创建数据库连接
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
                cid INT NOT NULL,
                pid INT NOT NULL,
                from_user INT NOT NULL,
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
                CREATE TRIGGER before_comment_insert
                BEFORE INSERT ON comments
                FOR EACH ROW
                BEGIN
                    DECLARE max_cid INT;
                    SET max_cid = (SELECT MAX(cid) FROM comments WHERE pid = NEW.pid);
                    IF max_cid IS NULL THEN
                        SET NEW.cid = 1;
                    ELSE
                        SET NEW.cid = max_cid + 1;
                    END IF;
                END;
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
                cid INT,
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
            -- 插入用户感兴趣的主题关系
            INSERT INTO interested_in_theme (uid, tid) VALUES 
            (1, 1), (1, 2), (1, 5),  -- Alice对Technology, Science, Gadgets感兴趣
            (2, 5), (2, 3),          -- Bob对Gadgets, Health感兴趣
            (3, 4), (3, 5),          -- Charlie对Travel, Gadgets感兴趣
            (4, 2), (4, 3), (4, 4),  -- David对Science, Health, Travel感兴趣
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5);  -- Eve对所有主题感兴趣
            """
            )

            # 插入评论数据
            cursor.execute(
                """
                -- 推文 1 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (1, 2, NULL, NULL, 'Very insightful article on AI!'),
                (1, 3, NULL, NULL, 'I think AI will change everything.'),
                (1, 4, NULL, NULL, 'What about the ethical implications?'),
                (1, 5, 1, 1, 'I agree, especially in healthcare applications.'),
                (1, 1, 1, 1, 'Also in autonomous vehicles!'),
                (1, 2, 3, 1, 'Great point about ethics. We need more regulation.');
                """
            )

            cursor.execute(
                """
                -- 推文 2 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (2, 1, NULL, NULL, 'Which smartphone do you recommend?'),
                (2, 3, NULL, NULL, 'I prefer the new iPhone.'),
                (2, 4, NULL, NULL, 'Android all the way!'),
                (2, 5, 2, 2, 'I agree, but the battery life could be better.'),
                (2, 2, 2, 2, 'The camera is amazing though.'),
                (2, 1, 4, 2, 'Battery life is a big issue for me.');
                """
            )

            cursor.execute(
                """
                -- 推文 3 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (3, 4, NULL, NULL, 'Quantum computing is fascinating!'),
                (3, 5, NULL, NULL, 'How soon until it''s mainstream?'),
                (3, 2, NULL, NULL, 'I''m still trying to wrap my head around it.'),
                (3, 1, 3, 3, 'Same here, the concepts are mind-bending.'),
                (3, 3, 3, 3, 'Start with basic qubits and work your way up.'),
                (3, 4, 3, 3, 'Any good resources for beginners?');
                """
            )

            cursor.execute(
                """
                -- 推文 4 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (4, 5, NULL, NULL, 'These wearables are getting so advanced.'),
                (4, 1, NULL, NULL, 'I use one for fitness tracking.'),
                (4, 2, NULL, NULL, 'The health monitoring features are impressive.'),
                (4, 3, 2, 2, 'Yes, they''ve helped me stay more active.'),
                (4, 4, 2, 2, 'Battery life is still a problem though.'),
                (4, 5, 2, 2, 'Agreed, needs improvement.');
                """
            )

            cursor.execute(
                """
                -- 推文 5 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (5, 1, NULL, NULL, 'Exciting times for space exploration!'),
                (5, 2, NULL, NULL, 'Mars colonization is next.'),
                (5, 3, NULL, NULL, 'What about the environmental impact?'),
                (5, 4, 1, 1, 'We need to balance exploration with sustainability.'),
                (5, 5, 1, 1, 'Agreed, but the potential benefits are huge.'),
                (5, 1, 1, 1, 'Let''s hope for responsible development.');
                """
            )

            cursor.execute(
                """
                -- 推文 6 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (6, 2, NULL, NULL, 'Nutrition is so important for energy levels.'),
                (6, 3, NULL, NULL, 'What''s your favorite healthy recipe?'),
                (6, 4, NULL, NULL, 'I love smoothies in the morning.'),
                (6, 5, 1, 1, 'Oatmeal with berries works for me.'),
                (6, 1, 1, 1, 'I''ve been into kale salads lately.'),
                (6, 2, 1, 1, 'Need to try that, thanks!');
                """
            )

            cursor.execute(
                """
                -- 推文 7 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (7, 3, NULL, NULL, 'So many amazing places to visit!'),
                (7, 4, NULL, NULL, 'I''m planning a trip next year.'),
                (7, 5, NULL, NULL, 'Any recommendations in Europe?'),
                (7, 1, 1, 1, 'I loved Italy, the food was incredible.'),
                (7, 2, 1, 1, 'New Zealand is stunning too.'),
                (7, 3, 1, 1, 'I''d love to go to Japan someday.');
                """
            )

            cursor.execute(
                """
                -- 推文 8 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (8, 4, NULL, NULL, 'Mental health awareness is so important.'),
                (8, 5, NULL, NULL, 'Meditation has helped me a lot.'),
                (8, 1, NULL, NULL, 'Talking to someone makes a big difference.'),
                (8, 2, 1, 1, 'I''ve started journaling, it''s therapeutic.'),
                (8, 3, 1, 1, 'Exercise is my go-to stress reliever.'),
                (8, 4, 1, 1, 'Same here, even a short walk helps.');
                """
            )

            cursor.execute(
                """
                -- 推文 9 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (9, 1, NULL, NULL, 'Planning a vacation can be stressful.'),
                (9, 2, NULL, NULL, 'Use a good travel app to organize everything.'),
                (9, 3, NULL, NULL, 'I always research local customs beforehand.'),
                (9, 4, 1, 1, 'Packing light is key for stress-free travel.'),
                (9, 5, 1, 1, 'Agreed, but don''t forget essentials!'),
                (9, 1, 1, 1, 'Check visa requirements early.');
                """
            )

            cursor.execute(
                """
                -- 推文 10 的评论
                INSERT INTO comments (pid, from_user, to_comment, master_comment, content) VALUES 
                (10, 2, NULL, NULL, 'Remote work is here to stay.'),
                (10, 3, NULL, NULL, 'I love the flexibility.'),
                (10, 4, NULL, NULL, 'But I miss the office interaction.'),
                (10, 5, 1, 1, 'Hybrid models seem to be the future.'),
                (10, 1, 1, 1, 'Agreed, balance is important.'),
                (10, 2, 1, 1, 'Productivity has actually increased for me.');
                """
            )

            # 插入评论点赞数据
            cursor.execute(
                """
                -- 推文 1 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (1, 1, 1), (3, 1, 1), (5, 1, 1),
                (2, 2, 1), (4, 2, 1),
                (3, 3, 1), (5, 3, 1),
                (4, 4, 1),
                (5, 5, 1),
                (2, 6, 1);
                """
            )

            cursor.execute(
                """
                -- 推文 2 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (3, 1, 2), (5, 1, 2),
                (1, 2, 2), (4, 2, 2),
                (2, 3, 2), (5, 3, 2),
                (3, 4, 2),
                (4, 5, 2),
                (1, 6, 2);
                """
            )

            cursor.execute(
                """
                -- 推文 3 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (2, 1, 3), (4, 1, 3),
                (1, 2, 3), (3, 2, 3),
                (5, 3, 3),
                (2, 4, 3),
                (3, 5, 3),
                (4, 6, 3);
                """
            )

            cursor.execute(
                """
                -- 推文 4 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (1, 1, 4), (5, 1, 4),
                (2, 2, 4), (3, 2, 4),
                (4, 3, 4),
                (5, 4, 4),
                (1, 5, 4),
                (3, 6, 4);
                """
            )

            cursor.execute(
                """
                -- 推文 5 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (2, 1, 5), (4, 1, 5),
                (1, 2, 5), (3, 2, 5),
                (5, 3, 5),
                (2, 4, 5),
                (3, 5, 5),
                (4, 6, 5);
                """
            )

            cursor.execute(
                """
                -- 推文 6 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (3, 1, 6), (5, 1, 6),
                (1, 2, 6), (4, 2, 6),
                (2, 3, 6),
                (5, 4, 6),
                (1, 5, 6),
                (3, 6, 6);
                """
            )

            cursor.execute(
                """
                -- 推文 7 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (4, 1, 7), (5, 1, 7),
                (1, 2, 7), (3, 2, 7),
                (2, 3, 7),
                (5, 4, 7),
                (1, 5, 7),
                (2, 6, 7);
                """
            )

            cursor.execute(
                """
                -- 推文 8 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (3, 1, 8), (5, 1, 8),
                (1, 2, 8), (4, 2, 8),
                (2, 3, 8),
                (5, 4, 8),
                (1, 5, 8),
                (3, 6, 8);
                """
            )

            cursor.execute(
                """
                -- 推文 9 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (2, 1, 9), (4, 1, 9),
                (1, 2, 9), (5, 2, 9),
                (3, 3, 9),
                (5, 4, 9),
                (1, 5, 9),
                (2, 6, 9);
                """
            )

            cursor.execute(
                """
                -- 推文 10 的评论点赞
                INSERT INTO like_comment (uid, cid, pid) VALUES 
                (3, 1, 10), (5, 1, 10),
                (1, 2, 10), (4, 2, 10),
                (2, 3, 10),
                (5, 4, 10),
                (1, 5, 10),
                (3, 6, 10);
                """
            )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    create_db()
