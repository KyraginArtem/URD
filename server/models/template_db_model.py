# server/models/template_db_model.py
import json

import pymssql

class TemplateDBModel:
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

        # Получаем данные ячеек и их конфигурации
        cell_data = self._execute_query(
            """SELECT TemplateCells.cell_name, TemplateCells.data,
                      TemplateCellConfigurations.background_color, TemplateCellConfigurations.height,
                      TemplateCellConfigurations.width, TemplateCellConfigurations.text_color,
                      TemplateCellConfigurations.font, TemplateCellConfigurations.format,
                      TemplateCellConfigurations.text_tilt, TemplateCellConfigurations.underline,
                      TemplateCellConfigurations.text_size, TemplateCellConfigurations.merger,
                      TemplateCellConfigurations.bold
               FROM TemplateCells
               LEFT JOIN TemplateCellConfigurations ON TemplateCells.cell_id = TemplateCellConfigurations.cell_id
               WHERE template_id = %s
               ORDER BY TemplateCells.cell_id""",
            (template_id,),
            fetch_all=True
        )

        cells = []
        for row in cell_data:
            cell_name = row["cell_name"]
            value = row["data"]
            config = {
                "background_color": row.get("background_color"),
                "height": row.get("height"),
                "width": row.get("width"),
                "text_color": row.get("text_color"),
                "font": row.get("font"),
                "format": row.get("format"),
                "text_tilt": row.get("text_tilt"),
                "underline": row.get("underline"),
                "text_size": row.get("text_size"),
                "merger": row.get("merger"),
                "bold": row.get("bold")
            }
            cells.append({
                "cell_name": cell_name,
                "value": value,
                "config": config
            })

        return row_count, col_count, background_color, cells

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

            # Удаляем все существующие данные ячеек и их конфигурации для данного шаблона
            cursor.execute(
                "DELETE FROM TemplateCellConfigurations WHERE cell_id IN (SELECT cell_id FROM TemplateCells WHERE template_id = %s)",
                (template_id,))
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

            # Удаляем конфигурации ячеек, связанные с шаблоном
            cursor.execute(
                "DELETE FROM TemplateCellConfigurations WHERE cell_id IN (SELECT cell_id FROM TemplateCells WHERE template_id = %s)",
                (template_id,))

            # Удаляем все существующие данные ячеек для данного шаблона
            cursor.execute("DELETE FROM TemplateCells WHERE template_id = %s", (template_id,))

            # Удаляем сам шаблон
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
        try:
            cells = json.loads(cell_data)
            for cell in cells:
                cell_name = cell['cell_name']
                value = cell['value']
                config = cell['config']

                # Сохраняем данные ячейки в таблице TemplateCells
                cursor.execute("""
                            INSERT INTO TemplateCells (template_id, cell_name, data)
                            VALUES (%s, %s, %s)
                        """, (template_id, cell_name, value))

                # Получаем cell_id для связи с таблицей конфигураций
                cursor.execute("SELECT cell_id FROM TemplateCells WHERE template_id = %s AND cell_name = %s",
                               (template_id, cell_name))
                cell_id = cursor.fetchone()['cell_id']

                # Сохраняем конфигурацию ячейки в таблице TemplateCellConfigurations
                cursor.execute("""
                    INSERT INTO TemplateCellConfigurations (cell_id, background_color, height, width,
                    text_color, font, format, text_tilt, underline, text_size, cell_name, merger, bold)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (cell_id, config.get('background_color'), config.get('height'), config.get('width'),
                      config.get('text_color'), config.get('font'), config.get('format'),
                      config.get('text_tilt'), config.get('underline'), config.get('text_size'), cell_name,
                      config.get('merger'), config.get('bold')))

            self.connection.commit()
            print("Все ячейки и их конфигурации успешно сохранены.")
        except pymssql.Error as e:
            print(f"Ошибка сохранения ячеек: {e}")
            self.connection.rollback()
        finally:
            cursor.close()