import pymysql

class MySQLDB:
    def __init__(self):
        # 连接刚才启动的 MySQL（注意密码是 123456）
        self.conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='123456',
            database='nutrition_db',
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()
        # 初始化建表（如果表不存在则创建）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question VARCHAR(255) NOT NULL,
                answer TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def search_faq(self, query):
        # 极简版：用 SQL 的 LIKE 做模糊匹配（真实生产中会用 BM25 算法或 Redis）
        sql = "SELECT answer FROM faq WHERE question LIKE %s LIMIT 1"
        # 只要问题包含用户的词汇，就算命中
        self.cursor.execute(sql, (f"%{query}%",))
        result = self.cursor.fetchone()
        if result:
            return result[0] # 返回答案
        return None # 没命中

    def insert_faq(self, question, answer):
        sql = "INSERT INTO faq (question, answer) VALUES (%s, %s)"
        self.cursor.execute(sql, (question, answer))
        self.conn.commit()