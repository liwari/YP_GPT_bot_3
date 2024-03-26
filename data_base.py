import sqlite3

DB_NAME = 'gpt'
DB_EXTENSION = 'db'
db_path = f'{DB_NAME}.{DB_EXTENSION}'


def prepare_database():
    connection = sqlite3.connect(db_path)
    cur = connection.cursor()

    create_user_data_table(cur)
    create_messages_data_table(cur)

    connection.commit()
    connection.close()


def create_user_data_table(cursor: sqlite3.Cursor):
    sql_query = f'CREATE TABLE IF NOT EXISTS user_data' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'user_name TEXT, ' \
                f'session_id INTEGER, ' \
                f'total_tokens TEXT)'

    cursor.execute(sql_query)


def create_messages_data_table(cursor: sqlite3.Cursor):
    sql_query = f'CREATE TABLE IF NOT EXISTS messages_data' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'session_id INTEGER, ' \
                f'role TEXT, ' \
                f'content TEXT, ' \
                f'number_tokens TEXT, ' \
                f'total_tokens TEXT)'

    cursor.execute(sql_query)


def insert_user_to_user_data_table(user_id, user_name):
    user_data = get_user_data(user_id)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if not user_data:
        sql_query = f'INSERT INTO user_data (user_id) VALUES ({user_id});'
        cursor.execute(sql_query)
        sql_query = f"UPDATE user_data SET user_name = ?, session_id = ? WHERE user_id = ?;"
        cursor.execute(sql_query, (user_name, 1, user_id,))
    else:
        sql_query = f"UPDATE user_data SET session_id = ? WHERE user_id = ?;"
        next_session_id = user_data['session_id'] + 1
        cursor.execute(sql_query, (next_session_id, user_id,))
    connection.commit()
    connection.close()


def update_user_data(user_id, column, value):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    sql_query = f"UPDATE user_data SET {column} = ? WHERE user_id = ?;"
    cursor.execute(sql_query, (value, user_id,))

    connection.commit()
    connection.close()


def add_message_data(user_id, role: str, content: str):
    user_data = get_user_data(user_id)
    session_id = user_data['session_id']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    sql_query = "INSERT INTO messages_data(user_id, role, content, session_id) VALUES(?, ?, ?, ?)"
    cursor.execute(sql_query, (user_id, role, content, session_id))

    connection.commit()
    connection.close()


def get_user_data(user_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    sql_query = "SELECT * FROM user_data WHERE user_id = ?;"
    cursor.execute(sql_query, (user_id,))
    selected_user_data = cursor.fetchone()
    connection.close()

    if selected_user_data:
        user_data = {
            'id': selected_user_data[0],
            'user_id': selected_user_data[1],
            'user_name': selected_user_data[2],
            'session_id': selected_user_data[3],
            'total_tokens': selected_user_data[4],
        }

        return user_data
    return None


def get_messages_data(user_id, session_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    sql_query = "SELECT * FROM messages_data WHERE user_id = ? AND session_id = ?;"
    cursor.execute(sql_query, (user_id, session_id,))
    messages_list = cursor.fetchall()
    connection.close()
    messages_data = []
    for message in messages_list:
        message_data = {
            'id': message[0],
            'user_id': message[1],
            'session_id': message[2],
            'role': message[3],
            'content': message[4],
            'number_tokens': message[5],
            'total_tokens': message[6],
        }
        messages_data.append(message_data)

    return messages_data


prepare_database()
