import pymssql

class DBModel:
    def __init__(self):
        # Подключаемся к базе данных MS SQL Server
        self.connection = pymssql.connect(
            server='localhost',
            database='DB_URD',
            as_dict=True
        )

    def get_user_by_credentials(self, username, password):
        try:
            # Создаем курсор для выполнения запроса
            cursor = self.connection.cursor()
            # Выполняем SQL-запрос для проверки учетных данных
            cursor.execute("SELECT * FROM Users WHERE name = %s AND password = %s", (username, password))
            # Извлекаем результат запроса
            user = cursor.fetchone()
            return user
        except pymssql.Error as e:
            # Обработка ошибки при выполнении запроса
            print(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            # Закрываем курсор
            cursor.close()
