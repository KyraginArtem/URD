# client/services/template_table_service.py
import json

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QTableWidgetItem

from client.services.abstract_table_service import AbstractTableService

class TemplateTableService(AbstractTableService):

    @staticmethod
    def merge_cells(table, top_row, bottom_row, left_col, right_col, main_value):
        merge_range = f"{TemplateTableService.generate_cell_name(top_row, left_col)}:" \
                      f"{TemplateTableService.generate_cell_name(bottom_row, right_col)}"

        # Объединение ячеек визуально с помощью метода mergeCells()
        table.setSpan(top_row, left_col, (bottom_row - top_row + 1), (right_col - left_col + 1))

        # Устанавливаем основное значение и добавляем атрибут объединения для ячейки
        cell_data = TemplateTableService.create_cell_data(main_value, is_merged=True, merge_range=merge_range)
        item = QTableWidgetItem(main_value)  # Отображаем только значение
        item.setData(Qt.UserRole, cell_data)  # Сохраняем полные данные как пользовательские данные
        item.setTextAlignment(Qt.AlignCenter)  # Центрируем текст в объединенной ячейке
        table.setItem(top_row, left_col, item)

        # Применяем обновления к каждой ячейке в объединенном диапазоне
        # Остальные ячейки становятся частью объединения и очищаются
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                if not (row == top_row and col == left_col):
                    table.setItem(row, col, None)  # Очистить ячейку, так как она теперь часть объединения

    @staticmethod
    def create_cell_data(value, is_merged=False, merge_range=None):
        cell_data = {
            "value": value,
            "merged": {
                "is_merged": is_merged,
                "merge_range": merge_range
            }
        }
        return json.dumps(cell_data)

    def fill_cell(self, cell_name, color):
        """Заполняет ячейку указанным цветом."""
        # Реализация логики заливки цвета
        return True

    def set_font_color(self, cell_name, font_color):
        """Задает цвет шрифта для конкретной ячейки."""
        # Реализация изменения цвета текста в ячейке
        return True

    @staticmethod
    def parse_table_data(data):
        """Парсит данные шаблона и возвращает список ячеек с индексами и значениями."""
        parsed_data = []
        for item in data:
            try:
                # Попробуем загрузить строку как JSON
                cell_data = json.loads(item)
                value = cell_data.get("value", "")
                merged_info = cell_data.get("merged", {})

                # Извлечение имени ячейки
                cell_name = cell_data.get("cell_name")
                if cell_name:
                    col_label = ''.join(filter(str.isalpha, cell_name))
                    row_label = ''.join(filter(str.isdigit, cell_name))

                    # Преобразуем буквенный заголовок столбца в индекс (например, A -> 0, B -> 1)
                    col_index = TemplateTableService.column_label_to_index(col_label)
                    row_index = int(row_label) - 1  # Преобразуем строковый номер в индекс (начиная с 0)

                    # Добавляем данные в список, включая информацию об объединении
                    parsed_data.append((row_index, col_index, value, merged_info))

            except json.JSONDecodeError:
                # Если строка не является JSON, парсим как обычную строку формата "A1:Значение"
                if ':' in item:
                    try:
                        cell_name, value = item.split(':', 1)
                        col_label = ''.join(filter(str.isalpha, cell_name))
                        row_label = ''.join(filter(str.isdigit, cell_name))

                        # Преобразуем буквенный заголовок столбца в индекс (например, A -> 0, B -> 1)
                        col_index = TemplateTableService.column_label_to_index(col_label)
                        row_index = int(row_label) - 1  # Преобразуем строковый номер в индекс (начиная с 0)

                        # Добавляем данные в список без информации об объединении
                        parsed_data.append((row_index, col_index, value, {}))
                    except ValueError as e:
                        print(f"Ошибка парсинга данных ячейки: {e}")

        return parsed_data

    @staticmethod
    def column_label_to_index(label):
        """Преобразует буквенный заголовок столбца (например, 'A', 'B', 'AA') в индекс."""
        label = label.upper()
        index = 0
        for i, char in enumerate(reversed(label)):
            index += (ord(char) - ord('A') + 1) * (26 ** i)
        return index - 1

    @staticmethod
    def generate_cell_name(row, col):
        """Генерирует имя ячейки, подобное Excel, на основе номера строки и столбца."""
        labels = []
        num_columns = col + 1
        while num_columns > 0:
            num_columns -= 1
            labels.append(chr(65 + (num_columns % 26)))
            num_columns //= 26

        row_label = str(row + 1)
        return f"{''.join(reversed(labels))}{row_label}"

    @staticmethod
    def collect_table_data(table_widget):
        """Собирает данные из таблицы и возвращает их в формате строки."""
        rows = table_widget.rowCount()
        cols = table_widget.columnCount()
        cell_data = ""

        for row in range(rows):
            for col in range(cols):
                item = table_widget.item(row, col)
                if item:
                    # Получаем полные данные из пользовательских данных
                    cell_value = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
                    cell_name = TemplateTableService.generate_cell_name(row, col)
                    cell_data += f"{cell_name}:{cell_value}\n"

        return cell_data

    @staticmethod
    def parse_cell_data(cell_data_str):
        """Парсит строку данных ячейки и возвращает объект с информацией о значении и свойствах."""
        try:
            cell_data = eval(cell_data_str)  # Преобразуем строку в словарь
            return cell_data
        except (SyntaxError, NameError) as e:
            print(f"Ошибка парсинга данных ячейки: {e}")
            return {
                "value": cell_data_str,
                "merged": {
                    "is_merged": False,
                    "merge_range": None
                }
            }

    @staticmethod
    def parse_merge_range(merge_range):
        """Парсит строку merge_range в координаты ячеек."""
        try:
            top_left, bottom_right = merge_range.split(":")
            top_row = int(''.join(filter(str.isdigit, top_left))) - 1
            left_col = TemplateTableService.column_label_to_index(''.join(filter(str.isalpha, top_left)))
            bottom_row = int(''.join(filter(str.isdigit, bottom_right))) - 1
            right_col = TemplateTableService.column_label_to_index(''.join(filter(str.isalpha, bottom_right)))
            return top_row, left_col, bottom_row, right_col
        except ValueError:
            return None, None, None, None