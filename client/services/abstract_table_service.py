# client/services/abstract_table_service.py

from abc import ABC, abstractmethod

class AbstractTableService(ABC):

    @staticmethod
    @abstractmethod
    def parse_table_data(data):
        """Парсит данные ячеек таблицы и возвращает удобный формат."""
        pass

    def merge_cells(self, start_cell, end_cell):
        """Метод для объединения ячеек, нужно будет определить индексы для начала и конца."""
        # Реализация логики объединения ячеек
        pass

    def fill_cell(self, cell_name, color):
        """Заполняет ячейку указанным цветом."""
        # Реализация логики заливки цвета
        pass

    def set_font_color(self, cell_name, font_color):
        """Задает цвет шрифта для конкретной ячейки."""
        # Реализация изменения цвета текста в ячейке
        pass
