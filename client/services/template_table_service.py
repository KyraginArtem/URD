# client/services/template_table_service.py
from client.services.abstract_table_service import AbstractTableService

class TemplateTableService(AbstractTableService):

    def merge_cells(self, start_cell, end_cell):
        """Метод для объединения ячеек, нужно будет определить индексы для начала и конца."""
        # Реализация логики объединения ячеек
        return True

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
            if ':' in item:
                cell_name, cell_value = item.split(':', 1)
                # Преобразуем имя ячейки в индексы строки и столбца
                col_label = ''.join(filter(str.isalpha, cell_name))
                row_label = ''.join(filter(str.isdigit, cell_name))
                # Преобразуем буквенный заголовок столбца в индекс (например, A -> 0, B -> 1)
                col_index = TemplateTableService.column_label_to_index(col_label)
                row_index = int(row_label) - 1  # Преобразуем строковый номер в индекс (начиная с 0)
                # Добавляем данные в список
                parsed_data.append((row_index, col_index, cell_value))
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
                cell_value = item.text() if item else ""
                cell_name = TemplateTableService.generate_cell_name(row, col)
                cell_data += f"{cell_name}:{cell_value}\n"

        return cell_data