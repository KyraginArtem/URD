# server/models/db_model.py
import json

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
            """SELECT TemplateCells.cell_name, TemplateCells.data, 
                      TemplateCellConfigurations.type, TemplateCellConfigurations.length, 
                      TemplateCellConfigurations.width, TemplateCellConfigurations.color, 
                      TemplateCellConfigurations.font, TemplateCellConfigurations.format, 
                      TemplateCellConfigurations.is_merged, TemplateCellConfigurations.merge_range
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
                "type": row.get("type"),
                "length": row.get("length"),
                "width": row.get("width"),
                "color": row.get("color"),
                "font": row.get("font"),
                "format": row.get("format"),
                "merged": {
                    "is_merged": row.get("is_merged", False),
                    "merge_range": row.get("merge_range")
                }
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
        """
        Сохраняет данные ячеек в базу данных. Ожидает, что cell_data - это JSON-строка с конфигурациями ячеек.
        """
        try:
            cells = json.loads(cell_data)  # Разбор JSON-строки
            for cell in cells:
                cell_name = cell.get("cell_name")
                cell_value = cell.get("value")

                cursor.execute("""
                    INSERT INTO TemplateCells (template_id, cell_name, data)
                    VALUES (%s, %s, %s)
                """, (template_id, cell_name, cell_value))

                # Получение ID сохраненной ячейки
                cell_id = cursor.lastrowid

                # Сохранение конфигурации ячейки
                config = cell.get("config")
                if config:
                    self.save_cell_configuration(template_id, cell_id, json.dumps(config))

            self.connection.commit()
            print("Все ячейки и их конфигурации успешно сохранены.")
        except pymssql.Error as e:
            print(f"Ошибка сохранения ячеек: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def save_cell_configuration(self, template_id, cell_id, config):
        """
        Сохраняет конфигурацию ячейки в таблицу TemplateCellConfigurations.
        :param template_id: ID шаблона.
        :param cell_id: ID ячейки.
        :param config: JSON-строка с конфигурацией ячейки.
        """
        try:
            cursor = self.connection.cursor()
            config_data = json.loads(config)  # Парсинг JSON-строки конфигурации

            # Установка значений по умолчанию для отсутствующих полей
            type_value = config_data.get("type", None)
            length_value = config_data.get("length", None)
            width_value = config_data.get("width", None)
            color_value = config_data.get("color", None)
            font_value = config_data.get("font", None)
            format_value = config_data.get("format", None)
            is_merged_value = config_data.get("is_merged", False)
            merge_range_value = config_data.get("merge_range", None)

            cursor.execute("""
                INSERT INTO TemplateCellConfigurations (cell_id, type, length, width, color, font, format, is_merged, merge_range)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cell_id,
                type_value,
                length_value,
                width_value,
                color_value,
                font_value,
                format_value,
                is_merged_value,
                merge_range_value
            ))

            self.connection.commit()
            print(f"Конфигурация ячейки успешно сохранена.")
            return True

        except pymssql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return False

        finally:
            cursor.close()
