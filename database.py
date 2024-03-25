import sqlite3
import os
# Создаем соединение с базой данных
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS chat_data (
        user_id INTEGER PRIMARY KEY,
        tokens INTEGER,
        session_id INTEGER,
        text TEXT,
        history TEXT
    )''')
def install_file(conn):
    c = conn.cursor()
    # Создаем таблицу, если ее еще нет
    c.execute('''CREATE TABLE IF NOT EXISTS chat_data (
        user_id INTEGER PRIMARY KEY,
        tokens INTEGER,
        session_id INTEGER,
        text TEXT,
        history TEXT
    )''')
    conn.close()

def delete_file(conn, file_path):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS {}".format(file_path))
    conn.commit()
# Функция для добавления новой строки в базу данных
def add_row(conn, user_id, tokens, session_id, text, history):
    c = conn.cursor()
    c.execute('''
            INSERT OR REPLACE INTO chat_data (user_id, tokens, session_id, text, history)
            VALUES (?,?, ?, ?, ?)
        ''', (user_id, tokens, session_id, text, history))
    # Сохраняем изменения
    conn.commit()

# Функция для обновления строки в базе данных по user_id
def update_row(conn,user_id, tokens, session_id, text, history):
    c = conn.cursor()
    query = f'''
        UPDATE chat_data
        SET tokens = ?, session_id = ?, text = ?, history = ?
        WHERE user_id = {user_id}
    '''
    # Выполняем запрос
    c.execute(query, (tokens, session_id, text, history))
    # Сохраняем изменения
    conn.commit()


def get_row(conn,user_id):
    c = conn.cursor()
    query = '''
        SELECT *
        FROM chat_data
        WHERE user_id = ?
    '''
    # Выполняем запрос
    c.execute(query, (user_id,))
    row = c.fetchone()


    # Возвращаем три переменные
    return row[1], row[2], row[3], row[4]

# Закрываем соединение с базой данных
conn.close()