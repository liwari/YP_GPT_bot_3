import sqlite3

DB_NAME = 'gpt'
DB_EXTENSION = 'db'
db_path = f'{DB_NAME}.{DB_EXTENSION}'


def prepare_database():
    connection = sqlite3.connect(db_path)
    cur = connection.cursor()

    sql_query = f'CREATE TABLE IF NOT EXISTS user_data' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'theme TEXT, ' \
                f'level TEXT, ' \
                f'task TEXT, ' \
                f'answer TEXT)'

    cur.execute(sql_query)
    connection.commit()
    connection.close()


def insert_user_to_user_data_table(user_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    user_data = get_user_data(user_id)
    if not user_data:
        sql_query = f'INSERT INTO user_data (user_id) VALUES ({user_id});'
        cursor.execute(sql_query)
    else:
        sql_query = f"UPDATE user_data SET theme = NULL, level = NULL, task = NULL, answer = NULL WHERE user_id = ?;"
        cursor.execute(sql_query, (user_id,))
    connection.commit()
    connection.close()


def update_user_data(user_id, column, value):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    sql_query = f"UPDATE user_data SET {column} = ? WHERE user_id = ?;"
    cursor.execute(sql_query, (value, user_id,))

    connection.commit()
    connection.close()


def get_user_data(user_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    sql_query = "SELECT * FROM user_data WHERE user_id = ?;"
    cursor.execute(sql_query, (user_id,))
    user_data = cursor.fetchone()
    connection.close()

    return user_data


prepare_database()
