import re
from server.models.report_db_model import ReportDBModel

class TemplateDatabaseService:
    def handle_parse(self, expression, time_start, time_end):
        if not expression.startswith("="):
            return expression

        # Удаляем знак "="
        expression = expression[1:]

        # Шаблоны для параметров
        tech_pattern = r"T\d+"  # Технологический параметр
        analytic_pattern = r"L\d+(?:\.\d+)?(?:\.\w+)?"  # Аналитический параметр
        xline_pattern = r"X\d+"  # X-линия

        # Поиск параметров
        tech_params = re.findall(tech_pattern, expression)
        analytic_params = re.findall(analytic_pattern, expression)
        xline_params = re.findall(xline_pattern, expression)

        #Если нашли шифр идем в БД
        tech_data = {}
        analytic_data = {}
        xline_data = {}
        if tech_params:
            tech_data = self.process_parameters(tech_params, "T", time_start, time_end)
        if analytic_params:
            analytic_data = self.process_parameters(analytic_params, "L", time_start, time_end)
        if xline_params:
            xline_data = self.process_parameters(xline_params, "X", time_start, time_end)

        # Обработка функций
        updated_expression, function_results = self.process_functions(expression, tech_data, analytic_data,
                                                                         xline_data)
        result = None
        #Условие для одного или массива значений
        if type(updated_expression) == str:
            # Операторы
            result = eval(updated_expression)
            print("Результат вычисления:", result)
        else:
            if tech_data != {}:
                result = tech_data
            elif analytic_data != {}:
                result = analytic_data
            elif xline_data != {}:
                result = analytic_data
        return result

    def process_parameters(self, params, type, time_start, time_end):
        # Ищем значения в БД
        # Параметр param_type определяет, какую таблицу использовать (T, L, X)
        result = {}
        value = None
        for param in params:

            #Запрос аналитичеких данных
            if type == "L":
                split_data = param[1:].split(".") # Остальные части
                data = {
                    "product" : split_data[0],
                    "index" : split_data[1],
                    "element": split_data[2]
                }
                db_name = "DB_NN_Analytical_data"
                db_model = ReportDBModel(db=db_name)
                value = db_model.get_analytical_value_element(data, time_start, time_end)

            #Запрос технологических данных
            elif type == "T":
                split_data = int(param[1:])  # Удаляем "T" и получаем ID
                data = {
                    "product" : split_data
                }
                db_name = "DB_NN_Technological_data"
                db_model = ReportDBModel(db=db_name)
                value = db_model.get_technological_value(data, time_start, time_end)

            #Запрос данных ручного ввода
            elif type == "X":
                split_data = int(param[1:])  # Удаляем "T" и получаем ID
                data = {
                    "product": split_data
                }
                db_name = "DB_NN_Xline_data"
                db_model = ReportDBModel(db=db_name)
                value = db_model.get_Xline_value(data, time_start, time_end)

            #Обрабатываем полученные данные
            value = self.get_value_in_list(value)
            result[param] = value
        return result

    def process_functions(self, expression, tech_data=None, analytic_data=None, xline_data=None):
        """
        Обрабатывает функции в строке, заменяет их результаты и возвращает обновлённое выражение.
        """
        # Устанавливаем значения по умолчанию, если данные не переданы
        tech_data = tech_data or {}
        analytic_data = analytic_data or {}
        xline_data = xline_data or {}

        # Поиск функций вида func(param)
        function_pattern = r"(\w+)\(([^)]+)\)"  # Ищет имя функции и её параметр
        functions = re.findall(function_pattern, expression)

        function_results = {}
        if functions:
            for func_name, func_param in functions:
                # Определяем, к какому типу данных относится параметр
                param_values = (
                        tech_data.get(func_param) or
                        analytic_data.get(func_param) or
                        xline_data.get(func_param) or []
                )

                # Если данных нет, решаем, что делать
                if not param_values:
                    print(f"Предупреждение: данные для функции {func_name}({func_param}) отсутствуют.")
                    result = 0  # Значение по умолчанию, если данных нет
                else:
                    # Обрабатываем функцию
                    if func_name == "last":
                        result = self.last(param_values)
                    elif func_name == "snm":
                        result = self.snm(param_values)
                    else:
                        # Если функция не реализована
                        raise ValueError(f"Функция '{func_name}' не поддерживается.")

                # Сохраняем результат функции
                function_results[f"{func_name}({func_param})"] = result
                # Заменяем функцию в строке на её результат
                expression = expression.replace(f"{func_name}({func_param})", str(result))
        else:
            function_results, expression = None, None
        return expression, function_results

    # -----------------------Функции-------------------------
    def last(self, values):
        """
        Возвращает последнее значение из списка или само значение, если оно одно.
        """
        if isinstance(values, list) and values:
            return values[-1]
        elif isinstance(values, (int, float)):
            return values
        return 0

    def snm(self, values):
        """
        Возвращает среднее значение из списка или 0, если список пуст.
        Универсально для любых элементов.
        """
        if not values:
            return 0
        return sum(values) / len(values)

    def get_value_in_list(self, valus):
        # Извлекаем все числовые значения, игнорируя ключ el_name
        numeric_values = []
        for entry in valus:
            for key, value in entry.items():
                if key != "el_name" and isinstance(value, (int, float)):  # Игнорируем ключ el_name
                    numeric_values.append(value)

        if not numeric_values:  # Если нет числовых значений
            return 0
        else:
            return numeric_values

# service = TemplateDatabaseService()
# # Пример использования
# formula = "=0.67 * snm(T430) * last(L300.3.Ni) / 100 + last(X432)"
# time_start = "2024-01-01 00:00:00"
# time_end = "2024-02-01 00:00:00"
# parsed_data = service.handle_parse(formula)
#
#
# tech_values = service.process_parameters(parsed_data["tech_params"], "T", time_start, time_end)
# analytic_values = service.process_parameters(parsed_data["analytic_params"], "L", time_start, time_end)
# xline_values = service.process_parameters(parsed_data["xline_params"], "X", time_start, time_end)
#
# print("Технологические параметры:", tech_values)
# print("Аналитические параметры:", analytic_values)
# print("X-линии:", xline_values)
