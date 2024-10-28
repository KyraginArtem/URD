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
        return self._execute_query(
            "SELECT * FROM Users WHERE name = %s AND password = %s",
            (username, password),
            fetch_one=True
        )

    def get_template_names(self):
        result = self._execute_query(
            "SELECT name FROM Templates",
            fetch_all=True
        )
        # Преобразуем результат в список строк
        template_names_list = [template['name'] for template in result] if result else []
        print(f"Названия шаблонов из базы данных: {template_names_list}")
        return template_names_list

    def get_template_info(self, template_name):
        template_info = self._execute_query(
            "SELECT template_id, row_count, column_count, background_color FROM Templates WHERE name = %s",
            (template_name,),
            fetch_one=True
        )
        if not template_info:
            return None

        row_count = template_info['row_count']
        col_count = template_info['column_count']
        background_color = template_info['background_color']
        template_id = template_info['template_id']

        # Получаем данные ячеек
        cell_data = self._execute_query(
            "SELECT cell_name, data FROM TemplateCells WHERE template_id = %s ORDER BY cell_id",
            (template_id,),
            fetch_all=True
        )
        cell_data_str = "\n".join(
            f"{row['cell_name']}:{row['data']}" for row in cell_data
        )
        return row_count, col_count, background_color, cell_data_str

    def save_template(self, template_name, row_count, col_count, cell_data, creation_date, background_color):
        try:
            cursor = self.connection.cursor()

            # Вставляем шаблон в таблицу Templates
            cursor.execute("""
                INSERT INTO Templates (name, creation_date, row_count, column_count, background_color)
                VALUES (%s, %s, %s, %s, %s)
            """, (template_name, creation_date, row_count, col_count, background_color))

            # Зафиксировать изменения
            self.connection.commit()

            # Получаем template_id для дальнейшего использования
            cursor.execute("SELECT template_id FROM Templates WHERE name = %s", (template_name,))
            template_id = cursor.fetchone()['template_id']

            # Сохраняем данные ячеек в таблице TemplateCells
            self._save_template_cells(cursor, template_id, cell_data)

            # Зафиксировать изменения
            self.connection.commit()
            print("Шаблон успешно сохранен в базе данных.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False

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

            # Получаем template_id для дальнейшего использования
            cursor.execute("SELECT template_id FROM Templates WHERE name = %s", (template_name,))
            template_id = cursor.fetchone()['template_id']

            # Удаляем все существующие данные ячеек для данного шаблона
            cursor.execute("DELETE FROM TemplateCells WHERE template_id = %s", (template_id,))

            self._save_template_cells(cursor, template_id, cell_data)

            self.connection.commit()

            print("Шаблон успешно обновлен в базе данных.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False

        finally:
            cursor.close()

    def delete_template(self, template_name):
        try:
            cursor = self.connection.cursor()

            # Получаем template_id для дальнейшего использования
            cursor.execute("SELECT template_id FROM Templates WHERE name = %s", (template_name,))
            template_id = cursor.fetchone()['template_id']

            cursor.execute("DELETE FROM TemplateCells WHERE template_id = %s", (template_id,))

            cursor.execute("DELETE FROM Templates WHERE name = %s", (template_name,))

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

    def template_exists(self, template_name):
        result = self._execute_query(
            "SELECT COUNT(*) AS count FROM Templates WHERE name = %s",
            (template_name,),
            fetch_one=True
        )
        return result and result['count'] > 0

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return None
        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            cursor.close()

    def _save_template_cells(self, cursor, template_id, cell_data):
        for cell in cell_data.split('\n'):
            if cell:
                cell_name, cell_value = cell.split(':')
                cursor.execute("""
                    INSERT INTO TemplateCells (template_id, cell_name, data)
                    VALUES (%s, %s, %s)
                """, (template_id, cell_name, cell_value))

