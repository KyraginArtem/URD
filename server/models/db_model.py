# server/models/db_model.py
import pymssql

class DBModel:
    def __init__(self):
        # Подключаемся к базе данных MS SQL Server
        self.connection = pymssql.connect(
            server='localhost',
            database='DB_URD',
            as_dict=True,
            charset='utf8'
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

    def get_template_data(self, template_name):
        try:
            # Создаем курсор для выполнения запроса
            cursor = self.connection.cursor()
            # Выполняем SQL-запрос для получения данных шаблона
            cursor.execute("SELECT * FROM TemplateCells WHERE template_id = (SELECT template_id FROM Templates WHERE name = %s)", (template_name,))
            # Извлекаем результат запроса
            template_data = cursor.fetchall()
            return template_data
        except pymssql.Error as e:
            # Обработка ошибки при выполнении запроса
            print(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            # Закрываем курсор
            cursor.close()

    def get_template_names(self):
        try:
            # Создаем курсор для выполнения запроса
            cursor = self.connection.cursor()
            # Выполняем SQL-запрос для получения всех шаблонов
            cursor.execute("SELECT name FROM Templates")
            # Извлекаем результаты запроса
            template_names = cursor.fetchall()
            print(f"Названия шаблонов из базы данных: {template_names}")  # Отладочное сообщение для проверки
            # Преобразуем результат в список строк
            template_names_list = [template['name'] for template in template_names]
            return template_names_list
        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []
        finally:
            # Закрываем курсор
            cursor.close()

    def get_template_info(self, template_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT row_count, column_count, background_color 
                FROM Templates 
                WHERE name = %s
            """, (template_name,))
            template_info = cursor.fetchone()
            print("Answer from DB")
            print(template_info)

            if not template_info:
                return None

            row_count = template_info['row_count']
            col_count = template_info['column_count']
            background_color = template_info['background_color']
            print(row_count, col_count, background_color)

            # Получаем данные ячеек
            cursor.execute("""
                SELECT data 
                FROM TemplateCells 
                WHERE template_id = (SELECT template_id FROM Templates WHERE name = %s)
                ORDER BY cell_id
            """, (template_name,))
            # cell_data = "\n".join([row['data'] for row in cursor.fetchall()])
            cell_data = "\n".join(
                [row['data'] if isinstance(row['data'], str) else row['data'].decode('utf-8') for row in
                 cursor.fetchall()])
            print("данные в ячейке")
            print(cell_data)

            return row_count, col_count, background_color, cell_data

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            cursor.close()

    def update_template(self, template_name, row_count, col_count, cell_data, creation_date, background_color):
        try:
            cursor = self.connection.cursor()

            # Обновляем данные о шаблоне в таблице Templates
            cursor.execute("""
                    UPDATE Templates
                    SET creation_date = %s, row_count = %s, column_count = %s, background_color = %s
                    WHERE name = %s
                """, (creation_date, row_count, col_count, background_color, template_name))

            # Зафиксировать изменения в таблице Templates
            self.connection.commit()

            # Удаляем все существующие данные ячеек для данного шаблона
            cursor.execute("""
                    DELETE FROM TemplateCells
                    WHERE template_id = (SELECT template_id FROM Templates WHERE name = %s)
                """, (template_name,))

            # Сохраняем новые данные ячеек в таблице TemplateCells
            for cell in cell_data.split('\n'):
                if cell:
                    cell_name, cell_value = cell.split(':')
                    cursor.execute("""
                            INSERT INTO TemplateCells (template_id, cell_name, data)
                            VALUES ((SELECT template_id FROM Templates WHERE name = %s), %s, %s)
                        """, (template_name, cell_name, cell_value))

            # Зафиксировать изменения в таблице TemplateCells
            self.connection.commit()

            print("Шаблон успешно обновлен в базе данных.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False  # Возвращаем False, если произошла ошибка

        finally:
            cursor.close()

    def save_template(self, template_name, row_count, col_count, cell_data, creation_date, background_color):
        try:
            cursor = self.connection.cursor()

            # Получаем текущую дату для `creation_date`

            # Выполняем SQL-запрос для вставки шаблона в таблицу Templates
            cursor.execute("""
                    INSERT INTO Templates (name, creation_date, row_count, column_count, background_color)
                    VALUES (%s, %s, %s, %s, %s)
                """, (template_name, creation_date, row_count, col_count, background_color))

            # Зафиксировать изменения в базе данных
            self.connection.commit()

            # Сохраняем данные ячеек в таблице TemplateCells
            for cell in cell_data.split('\n'):
                if cell:
                    cell_name, cell_value = cell.split(':')
                    cursor.execute("""
                            INSERT INTO TemplateCells (template_id, cell_name, data)
                            VALUES ((SELECT template_id FROM Templates WHERE name = %s), %s, %s)
                        """, (template_name, cell_name, cell_value))

            # Зафиксировать изменения
            self.connection.commit()

            print("Шаблон успешно сохранен в базе данных.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False  # Возвращаем False, если произошла ошибка

        finally:
            cursor.close()

    def template_exists(self, template_name):
        try:
            cursor = self.connection.cursor(as_dict=False)  # Создаем курсор без использования словаря
            query = "SELECT COUNT(*) AS count FROM Templates WHERE name = %s"
            cursor.execute(query, (template_name,))
            result = cursor.fetchone()

            # Проверяем, удалось ли получить результат
            if result and result[0] > 0:
                return True
            else:
                return False
        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False
        finally:
            cursor.close()

    def delete_template(self, template_name):
        try:
            cursor = self.connection.cursor()

            # Удаление всех ячеек, связанных с шаблоном
            cursor.execute("""
                DELETE FROM TemplateCells 
                WHERE template_id = (SELECT template_id FROM Templates WHERE name = %s)
            """, (template_name,))

            # Удаление самого шаблона
            cursor.execute("""
                DELETE FROM Templates 
                WHERE name = %s
            """, (template_name,))

            # Зафиксировать изменения в базе данных
            self.connection.commit()

            print(f"Шаблон '{template_name}' успешно удален из базы данных.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False

        finally:
            cursor.close()

