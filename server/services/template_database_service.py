# server/services/template_database_service.py

import re
from collections import defaultdict

from server.models.report_db_model import ReportDBModel

class TemplateDatabaseService:
    def handle_parse(self, expression, time_start, time_end):
        if not expression.startswith("="):
            return expression

        # Удаляем знак "="
        expression = expression[1:]

        tech_data = {}
        analytic_data = {}
        xline_data = {}
        result_cipher_processing = defaultdict(list)

        #Простые запросы ---------------------------------------------------------
        getNameProd_pattern = r"getNameProd\((L|X|T)(\d+)\)"
        getUnitProd_pattern = r"getUnitProd\((X|T)(\d+)\)"
        getNamePrd_params = re.match(getNameProd_pattern, expression)
        getUnitPrd_params = re.match(getUnitProd_pattern, expression)
        # Запрос имени продукта
        if getNamePrd_params:
            value = [getNamePrd_params.group(1), getNamePrd_params.group(2)]
            return self.get_name_prod(value)
        # Запрос имени продукта
        if getUnitPrd_params:
            value = [getUnitPrd_params.group(1), getUnitPrd_params.group(2)]
            return self.get_unit_prod(value)

        # находим сразу функции получения начальной и конечной даты
        if expression == "end_date()":
            return time_end
        elif expression == "start_date()":
            return time_start
        #-------------------------------------------------------------------------------

        # Шаблоны для запросов данных из БД параметров
        tech_pattern = r"(?<!\w)T[A-Za-z0-9_]+(?!\w)"  # Технологический параметр
        analytic_pattern = r"L\d+(?:\.\d+)?(?:\.\w+)?(?:\.[PQT])?"  # Аналитический параметр
        xline_pattern = r"(?<!\w)X[A-Za-z0-9_]+(?!\w)"  # X-линия

        # Поиск параметров
        tech_params = re.findall(tech_pattern, expression)
        analytic_params = re.findall(analytic_pattern, expression)
        xline_params = re.findall(xline_pattern, expression)

        #Если нашли шифр идем в БД
        if tech_params:
            for element in tech_params:
                result = self.process_parameters(element, "T", time_start, time_end)
                result_cipher_processing[element].append(result)

        if analytic_params:
            for element in analytic_params:
                result = self.process_parameters(element, "L", time_start, time_end)
                result_cipher_processing[element].append(result)

        if xline_params:
            for element in xline_params:
                result = self.process_parameters(element, "X", time_start, time_end)
                result_cipher_processing[element].append(result)

        #меняем шифры на полученные данные
        expression = self.replace_ciphers(expression, result_cipher_processing)

        # Обработка функций
        updated_expression = self.process_functions(expression, time_start, time_end)

        error_check = self.is_computable_math_expression(updated_expression)
        if error_check is True:
            # Если выражение вычисляется, возвращаем результат
            return eval(updated_expression)
        else:
            # Возвращаем сообщение об ошибке
            return error_check

    def replace_ciphers(self, expression, result_cipher_processing):
        """
        Заменяет шифры в строке на соответствующие данные из result_cipher_processing.

        :param expression: Исходная строка с шифрами.
        :param result_cipher_processing: Словарь с данными для шифров.
        :return: Строка с замененными шифрами на данные.
        """


        analytic_pattern = r"L\d+(?:\.\d+)?(?:\.\w+)?(?:\.[PQT])?"
        tech_pattern = r"(?<!\w)T[A-Za-z0-9_]+(?!\w)"
        xline_pattern = r"(?<!\w)X[A-Za-z0-9_]+(?!\w)"
        analytic_params = re.findall(analytic_pattern, expression)
        tech_params = re.findall(tech_pattern, expression)
        xline_params = re.findall(xline_pattern, expression)

        all_ciphers = analytic_params + tech_params + xline_params
        print("All params:", all_ciphers)

        # Проходим по каждому шифру и заменяем его
        for cipher in all_ciphers:
            if cipher in result_cipher_processing:
                # Берем первое значение из списка данных
                replacement = result_cipher_processing[cipher].pop(0)

                # Проверяем, что это за значение
                if isinstance(replacement, list):
                    replacement_str = str(replacement)  # Преобразуем список в строку
                elif isinstance(replacement, str):
                    replacement_str = f"[ERROR: {replacement}]"  # Ошибка как строка
                else:
                    replacement_str = str(replacement)  # Другое значение

                # Заменяем только первое вхождение шифра
                expression = expression.replace(cipher, replacement_str, 1)

        return expression

    def process_parameters(self, param, type, time_start, time_end):
        # Ищем значения в БД
        # Параметр param_type определяет, какую таблицу использовать (T, L, X)
        value = []


        # Запрос аналитичеких данных
        if type == "L":
            split_data = param[1:].split(".")  # Остальные части
            if len(split_data) < 3:
                result = "Ошибка ввода"
                return result
            data = {
                "product": split_data[0],
                "level": split_data[1],
                "element": split_data[2],
            }
            if len(split_data) > 3:
                parm_type = split_data[3]

                if parm_type == "P":
                    db_name = "DB_NN_Analytical_data"
                    db_model = ReportDBModel(db=db_name)
                    value = db_model.get_analytical_value_element(data, time_start, time_end)
                elif parm_type == "Q":
                    db_name = "DB_NN_Analytical_data"
                    db_model = ReportDBModel(db=db_name)
                    value = db_model.get_analytical_value_tonnage(data, time_start, time_end)
            else:
                return "Ошибка ввода"

        # Запрос технологических данных
        elif type == "T":
            split_data = param[1:]  # Удаляем "T" и получаем ID

            # проверяем корректный ввод шифра
            if not self.is_valid_number(split_data):
                return "Ошибка ввода"

            data = {
                "product": split_data
            }
            db_name = "DB_NN_Technological_data"
            db_model = ReportDBModel(db=db_name)
            value = db_model.get_technological_value(data, time_start, time_end)

        # Запрос данных ручного ввода
        elif type == "X":
            split_data = param[1:]  # Удаляем "X" и получаем ID

            # проверяем корректный ввод шифра
            if not self.is_valid_number(split_data):
                return "Ошибка ввода"

            data = {
                "product": split_data
            }
            db_name = "DB_NN_Xline_data"
            db_model = ReportDBModel(db=db_name)
            value = db_model.get_Xline_value(data, time_start, time_end)

            #Обрабатываем полученные данные
        return self.get_value_in_list(value)



    def process_functions(self, expression, time_start, time_end):
        """
        Обрабатывает функции в строке, заменяет их результаты и возвращает обновлённое выражение.
        """
        # Поиск функций вида func(param)
        function_pattern = r"(\w+)\(\s*([^)]*)\s*\)" # Ищет имя функции и её параметр
        functions = re.findall(function_pattern, expression)

        function_results = {}
        if functions:
            for func_name, func_param in functions:

                # Если параметр содержит ошибку, пропускаем обработку этой функции
                if "[ERROR:" in func_param:
                    print(f"Пропуск функции {func_name}({func_param}) из-за ошибки в параметре.")
                    function_results[f"{func_name}({func_param})"] = func_param
                    continue
                try:
                    # Обрабатываем функцию
                    if func_name == "lst":
                        result = self.lst(eval(func_param))

                    elif func_name == "ave":
                        result = self.ave(eval(func_param))

                    elif func_name == "snm":
                        result = self.snm(eval(func_param))

                    elif func_name == "count":
                        result = len(eval(func_param))

                    elif func_name == "max":
                        result = max(eval(func_param))

                    elif func_name == "min":
                        result = min(eval(func_param))

                    elif func_name == "sum":
                        result = sum(eval(func_param))

                    elif func_name == "tave":
                        param_values = eval(func_param)
                        result = self.tave(eval(param_values), len(param_values))
                    else:
                        # Если функция не поддерживается
                        result = f"[ERROR: Функция '{func_name}' не поддерживается]"
                except Exception:
                    # Обработка ошибок выполнения функции
                    result = f"[ERROR: Ошибка ввода]"

                # Заменяем функцию в строке на её результат
                expression = expression.replace(f"{func_name}({func_param})", str(result))
        else:
            return expression
        return expression

    # -----------------------Функции-------------------------
    def lst(self, values):
        """
        Возвращает последнее значение из списка или само значение, если оно одно.
        """
        if isinstance(values, list) and values:
            return values[-1]
        elif isinstance(values, (int, float)):
            return values
        return 0

    def ave(self, values):
        """
        Возвращает среднее значение из списка или 0, если список пуст.
        Универсально для любых элементов.
        """
        if not values:
            return 0
        result = sum(values) / len(values)
        return result

    def snm(self, values):
        """
        Возвращает первое достоверное значение из списка.
        """
        if isinstance(values, list) and values:
            return values[0]
        elif isinstance(values, (int, float)):
            return values
        return 0

    def tave(self, values, total_count):
        """
        Среднее всех значений за период (с учетом полного количества значений).
        TAVE = сумма достоверных значений / полное количество значений.
        """
        if not values or total_count == 0:
            return 0
        return sum(values) / total_count

    def get_value_in_list(self, values):
        # Извлекаем все числовые значения, игнорируя ключ el_name
        numeric_values = []
        for entry in values:
            for key, value in entry.items():
                if key != "el_name" and isinstance(value, (int, float)):  # Игнорируем ключ el_name
                    numeric_values.append(value)

        if not numeric_values:  # Если нет числовых значений
            return 0
        else:
            return numeric_values

    def get_name_prod(self, value):
        # Запрос аналитичеких данных
        if value[0] == "L":
            data = value[1]
            db_name = "DB_NN_Analytical_data"
            db_model = ReportDBModel(db=db_name)
            return db_model.get_name_product_analytical(data)
        # Запрос технологических данных
        elif value[0] == "T":
            data = value[1]
            db_name = "DB_NN_Technological_data"
            db_model = ReportDBModel(db=db_name)
            return db_model.get_name_product_technological(data)
        # Запрос данных ручного ввода
        elif value[0] == "X":
            data = value[1]
            db_name = "DB_NN_Xline_data"
            db_model = ReportDBModel(db=db_name)
            return db_model.get_name_product_Xline(data)

    def get_unit_prod(self, value):
        # Запрос технологических данных
        if value[0] == "T":
            data = value[1]
            db_name = "DB_NN_Technological_data"
            db_model = ReportDBModel(db=db_name)
            return db_model.get_unit_product_technological(data)

        # Запрос данных ручного ввода
        elif value[0] == "X":
            data = value[1]
            db_name = "DB_NN_Xline_data"
            db_model = ReportDBModel(db=db_name)
            return db_model.get_unit_product_Xline(data)

    def is_valid_number(self, data):
        input_str = str(data).strip()  # Убираем пробелы по краям
        pattern = r"^\d+$"
        match = re.match(pattern, input_str)
        print(f"Проверка: {data} -> {input_str} -> {bool(match)}")  # Отладочный вывод
        return bool(match)

    def is_computable_math_expression(self, expression):
        """
        Проверяет, можно ли вычислить математическое выражение, и возвращает результат или сообщение об ошибке.
        """
        try:
            eval(expression)  # Проверяем, вычисляется ли выражение
            return True
        except SyntaxError:
            return "[ERROR: Синтаксическая ошибка в выражении]"
        except ZeroDivisionError:
            return "[ERROR: Деление на ноль]"
        except NameError:
            return "[ERROR: Некорректное имя переменной или функции]"
        except Exception as e:
            return f"[ERROR: Неизвестная ошибка: {str(e)}]"

# service = TemplateDatabaseService()
#
# # Пример использования
# formula = "=0.67 * snm(T430) * last(L300.3.Ni) / 100 + last(X432)"  getNameProd(L300), getNameProd(X432), getNameProd(T430)
# time_start = "2024-01-01 00:00:00"
# time_end = "2024-02-01 00:00:00"
# result = service.handle_parse(formula, time_start, time_end)
#
#
# # tech_values = service.process_parameters(parsed_data["tech_params"], "T", time_start, time_end)
# # analytic_values = service.process_parameters(parsed_data["analytic_params"], "L", time_start, time_end)
# # xline_values = service.process_parameters(parsed_data["xline_params"], "X", time_start, time_end)
#
# print("Технологические параметры:", result)
# print("Аналитические параметры:", analytic_values)
# print("X-линии:", xline_values)
