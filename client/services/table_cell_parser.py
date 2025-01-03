# client/services/table_cell_parser.py

import re
import operator

from client.services.template_table_service import TemplateTableService

class TableCellParser:
    OPERATORS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv
    }

    @staticmethod
    def parse_formula(formula, table):
        """
        Парсит формулу и выполняет вычисление.
        :param formula: Строка формулы (например, "=A1+A2")
        :param table: QTableWidget для доступа к значениям ячеек
        :return: Результат вычислений
        """
        # Убираем знак "="
        if not formula.startswith("="):
            raise ValueError("Формула должна начинаться с '='")
        formula = formula[1:]

        # Регулярное выражение для разбиения на операнды и операторы
        tokens = re.split(r'(\+|\-|\*|/)', formula)
        if len(tokens) < 3:
            raise ValueError("Неправильный формат формулы")

        # Получение операндов и оператора
        operand1, operator, operand2 = tokens[0].strip(), tokens[1].strip(), tokens[2].strip()

        # Преобразуем A1, A2 и т.п. в индексы строки и столбца
        row1, col1 = TemplateTableService.parse_cell_position(operand1)
        row2, col2 = TemplateTableService.parse_cell_position(operand2)

        # Получаем значения из таблицы
        value1 = TableCellParser.get_cell_value(table, row1, col1)
        value2 = TableCellParser.get_cell_value(table, row2, col2)

        # Проверяем оператор и выполняем вычисление
        if operator in TableCellParser.OPERATORS:
            try:
                return TableCellParser.OPERATORS[operator](value1, value2)
            except ZeroDivisionError:
                raise ValueError("Деление на ноль")
        else:
            raise ValueError(f"Неподдерживаемый оператор: {operator}")

    @staticmethod
    def get_cell_value(table, row, col):
        """
        Возвращает значение ячейки как число.
        """
        item = table.item(row, col)
        if item and item.text().strip().isdigit():
            return float(item.text().strip())
        raise ValueError(f"Значение в ячейке ({row}, {col}) не является числом")
