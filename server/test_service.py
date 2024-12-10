from services.template_database_service import TemplateDatabaseService
from models.report_db_model import ReportDBModel

def test_service():
    # Создаем экземпляры сервиса и модели
    db_name = "DB_NN_Analytical_data"  # Укажите имя вашей базы данных
    service = TemplateDatabaseService()
    db_model = ReportDBModel(db=db_name)

    # Задаем тестовые данные
    test_expressions = [
        "=L301.3.H2SO4",  # Аналитический запрос
    ]
    time_start = "2024-04-18 00:00:00"
    time_end = "2024-04-18 00:00:00"

    for expression in test_expressions:
        print(f"Тестируем выражение: {expression}")
        try:
            # Парсим и обрабатываем выражение
            result = service.handle_parse(expression, time_start, time_end)
            print(f"Результат для '{expression}': {result}")
        except Exception as e:
            print(f"Ошибка при обработке выражения '{expression}': {e}")

def test_db_model():
    # Создаем экземпляр модели
    db_name = "DB_NN_Analytical_data"  # Укажите имя вашей базы данных
    db_model = ReportDBModel(db=db_name)

    # Тестовые данные
    analytical_data = {
        "product": "301",
        "index": "3",
        "element": "H2SO4"
    }

    time_start = "2024-04-18 00:00:00"
    time_end = "2024-04-18 00:00:00"

    try:
        # Тестируем аналитические данные
        print("Тестируем прямой запрос к БД аналитических данных...")
        analytical_result = db_model.get_analytical_value_element(analytical_data, time_start, time_end)
        print("Результат аналитических данных функции get_analytical_value:", analytical_result)

        # # Тестируем технологические данные
        # print("Тестируем технологические данные...")
        # technological_result = db_model.get_technological_value(technological_data, time_start, time_end)
        # print("Результат технологических данных:", technological_result)
        #
        # # Тестируем данные ручного ввода
        # print("Тестируем данные ручного ввода...")
        # xline_result = db_model.get_Xline_value(xline_data, time_start, time_end)
        # print("Результат данных ручного ввода:", xline_result)

    except Exception as e:
        print(f"Ошибка при выполнении запросов к БД: {e}")

if __name__ == "__main__":
    print("=== Тестирование сервиса TemplateDatabaseService ===")
    test_service()
    print("\n=== Тестирование модели ReportDBModel ===")
    test_db_model()
