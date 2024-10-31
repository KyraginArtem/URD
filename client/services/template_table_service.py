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

        # Объединение ячеек визуально с помощью метода setSpan()
        table.setSpan(top_row, left_col, (bottom_row - top_row + 1), (right_col - left_col + 1))

        # Устанавливаем основное значение и добавляем атрибут объединения для ячейки
        cell_data = TemplateTableService.create_cell_data(main_value, is_merged=True, merge_range=merge_range)
        item = QTableWidgetItem(main_value)  # Отображаем только значение
        item.setData(Qt.UserRole, cell_data)  # Сохраняем полные данные как пользовательские данные
        item.setTextAlignment(Qt.AlignCenter)  # Центрируем текст в объединенной ячейке
        table.setItem(top_row, left_col, item)

        # Очищаем остальные ячейки в диапазоне
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
                    # Попытка получить полные данные из пользовательских данных
                    cell_data_str = item.data(Qt.UserRole)
                    if cell_data_str:
                        try:
                            cell_data_json = json.loads(cell_data_str)
                            cell_value = cell_data_json.get("value", "")
                        except json.JSONDecodeError:
                            cell_value = item.text()  # Если не удалось, берем обычный текст
                    else:
                        cell_value = item.text() if item else ""

                    cell_name = TemplateTableService.generate_cell_name(row, col)
                    cell_data += f"{cell_name}:{cell_value}\n"

        return cell_data

    @staticmethod
    def unmerge_cells(table, top_row, bottom_row, left_col, right_col):
        # Считываем текущее значение основной ячейки (левой верхней)
        main_item = table.item(top_row, left_col)
        if main_item:
            cell_data_str = main_item.data(Qt.UserRole)
            if cell_data_str:
                try:
                    cell_data = json.loads(cell_data_str)
                    main_value = cell_data.get("value", "")
                except json.JSONDecodeError:
                    main_value = ""
            else:
                main_value = ""
        else:
            main_value = ""

        # Отменяем объединение ячеек
        table.setSpan(top_row, left_col, 1, 1)

        # Восстанавливаем каждую ячейку в диапазоне
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                if row == top_row and col == left_col:
                    # Левой верхней ячейке присваиваем основное значение
                    new_item = QTableWidgetItem(main_value)
                else:
                    # Остальные ячейки делаем пустыми
                    new_item = QTableWidgetItem("")
                new_item.setData(Qt.UserRole, json.dumps({"value": new_item.text()}))
                table.setItem(row, col, new_item)

    @staticmethod
    def is_merged(table, top_row, left_col):
        item = table.item(top_row, left_col)
        if item:
            cell_data = item.data(Qt.UserRole)
            if cell_data:
                try:
                    cell_data_json = json.loads(cell_data)
                    return cell_data_json.get("merged", {}).get("is_merged", False)
                except json.JSONDecodeError:
                    return False
        return False

    @staticmethod
    def refresh_table_view(table, template_data):
        """Обновляет таблицу с данными из шаблона"""
        try:
            parts = template_data.split("|")
            if len(parts) < 4:
                raise ValueError("Invalid data format received from server.")

            row_count = int(parts[0].strip())
            col_count = int(parts[1].strip())
            background_color = parts[2].strip()
            cell_data = parts[3]
            cell_data_lines = cell_data.splitlines()

            table.setRowCount(row_count)
            table.setColumnCount(col_count)
            column_labels = [TemplateTableService.generate_cell_name(0, col) for col in range(col_count)]
            table.setHorizontalHeaderLabels(column_labels)
            table.setVerticalHeaderLabels([str(i + 1) for i in range(row_count)])

            # Обновляем фон таблицы
            table.setStyleSheet(f"background-color: {background_color};")

            # Парсим данные и обновляем таблицу
            parsed_data = TemplateTableService.parse_table_data(cell_data_lines)
            TemplateTableService.update_table_data(table, parsed_data)
        except ValueError as e:
            print(f"Error parsing template data: {e}")

    @staticmethod
    def update_table_data(table, parsed_data):
        """Обновляет данные таблицы на основе переданных данных"""
        table.clearContents()
        for row_index, col_index, value, merged_info in parsed_data:
            item = QTableWidgetItem(value)
            if merged_info and merged_info.get("is_merged"):
                item.setData(Qt.UserRole, json.dumps(merged_info))
            table.setItem(row_index, col_index, item)