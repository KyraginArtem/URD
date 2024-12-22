# server/models/report_db_model.py

import pymssql

class ReportDBModel:
    def __init__(self, db, param=None):
        self.db = db
        self.param = param
        self.connection = pymssql.connect(
            server='localhost',
            database=self.db,
            as_dict=True,
            charset='cp1251'
        )

    def get_analytical_value_tonnage(self, data, time_start, time_end):
        query = f"""
            SELECT Q
            FROM dbo.Lab_data
            WHERE PROD_ID = {data['product']}
              AND LEVEL_ID = {data['level']}
              AND PROD_TIME BETWEEN '{time_start}' AND '{time_end}';
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_analytical_value_element(self, data, time_start, time_end):
        query = f"""
            -- Определяем позиции элементов для конкретного SEQ_ID, связанного с продуктом и уровнем
            WITH ElementPositions AS (
                SELECT 
                    ls.el_vpos, -- Позиция элемента в таблице lab_data (например, EL1, EL2 и т.д.)
                    le.el_name  -- Имя элемента (например, SO2, H2SO4 и т.д.)
                FROM 
                    lab_sequences ls
                INNER JOIN 
                    lab_elements le ON le.el_id = ls.el_id -- Соединяем последовательности с элементами
                WHERE 
                    ls.seq_id = (
                        -- Получаем SEQ_ID для указанного продукта, уровня и временного интервала
                        SELECT DISTINCT ld.seq_id
                        FROM lab_data ld
                        WHERE 
                            ld.prod_id = {data["product"]} -- Фильтрация по продукту (например, 301)
                            AND ld.level_id = {data["level"]} -- Фильтрация по уровню (например, 3)
                            AND ld.prod_time BETWEEN '{time_start}' AND '{time_end}' -- Фильтрация по времени
                    )
                    AND le.el_name = '{data["element"]}' -- Фильтрация по имени элемента (например, H2SO4)
            )
            -- Получаем значение элемента из таблицы lab_data на основе позиции элемента (el_vpos)
            SELECT 
                ep.el_name, -- Имя элемента
                CASE ep.el_vpos
                    WHEN 1 THEN ld.el1 -- Если позиция элемента = 1, берем значение из колонки EL1
                    WHEN 2 THEN ld.el2 -- Если позиция элемента = 2, берем значение из колонки EL2
                    WHEN 3 THEN ld.el3
                    WHEN 4 THEN ld.el4
                    WHEN 5 THEN ld.el5
                    WHEN 6 THEN ld.el6
                    WHEN 7 THEN ld.el7
                    WHEN 8 THEN ld.el8
                    WHEN 9 THEN ld.el9
                    WHEN 10 THEN ld.el10
                    WHEN 11 THEN ld.el11
                    WHEN 12 THEN ld.el12
                    WHEN 13 THEN ld.el13
                    WHEN 14 THEN ld.el14 -- Если позиция элемента = 14, берем значение из колонки EL14
                END AS element_value -- Значение элемента
            FROM 
                ElementPositions ep -- Используем ранее определенные позиции элементов
            INNER JOIN 
                lab_data ld ON ld.prod_id = {data["product"]} -- Фильтрация по продукту
                AND ld.level_id = {data["level"]} -- Фильтрация по уровню
                AND ld.prod_time BETWEEN '{time_start}' AND '{time_end}'; -- Фильтрация по времени
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_technological_value(self, data, time_start, time_end):
        # Формирование SQL-запроса для технологических данных
        query = f"""
            SELECT 
                td.PAR_VALUE
            FROM 
                dbo.Tech_data_day td
            JOIN 
                dbo.Tech_time_day ttd ON td.PAR_TIME_ID = ttd.PAR_TIME_ID
            WHERE 
                td.PAR_ID = {data["product"]}  -- ID продукта
                AND ttd.PAR_TIME BETWEEN '{time_start}' AND '{time_end}';
            """
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_Xline_value(self, data, time_start, time_end):
        # Формирование SQL-запроса для технологических данных
        query = f"""
            SELECT 
                td.PAR_VALUE
            FROM 
                dbo.Xline_data_day td
            JOIN 
                dbo.Xline_time_day ttd ON td.PAR_TIME_ID = ttd.PAR_TIME_ID
            WHERE 
                td.PAR_ID = {data["product"]}  -- ID продукта
                AND ttd.PAR_TIME BETWEEN '{time_start}' AND '{time_end}';
            """
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_name_product_analytical(self, prod_id):
        query = f"""
            SELECT PROD_NAME
            FROM dbo.Lab_products
            WHERE PROD_ID = %s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query, (prod_id,))
            result = cursor.fetchone()  # Используем fetchone для одного результата
            if result is None:  # Проверяем, что результат отсутствует
                return "[ERROR: Ошибка в выражении]"
            return result['PROD_NAME']

    def get_name_product_technological(self, par_id):
        query = f"""
                    SELECT NAME
                    FROM dbo.Tech_config
                    WHERE PAR_ID = %s
                """
        with self.connection.cursor() as cursor:
            cursor.execute(query, (par_id,))
            result = cursor.fetchone()  # Используем fetchone для одного результата
            if result is None:  # Проверяем, что результат отсутствует
                return "[ERROR: Ошибка в выражении]"
            return result['NAME']

    def get_name_product_Xline(self, par_id):
        query = f"""
                    SELECT NAME
                    FROM dbo.Xline_config
                    WHERE PAR_ID = %s
                """
        with self.connection.cursor() as cursor:
            cursor.execute(query, (par_id,))
            result = cursor.fetchone()  # Используем fetchone для одного результата
            if result is None:  # Проверяем, что результат отсутствует
                return "[ERROR: Ошибка в выражении]"
            return result['NAME']

    def get_unit_product_technological(self, par_id):
        query = f"""
                    SELECT u.UNIT_NAME
                    FROM dbo.Units u
                    WHERE u.UNIT_ID = (
                    SELECT xc.UNIT
                    FROM dbo.Tech_config xc
                    WHERE xc.PAR_ID = %s
                    )
                """
        with self.connection.cursor() as cursor:
            cursor.execute(query, (par_id,))
            result = cursor.fetchone()  # Используем fetchone для одного результата
            if result is None:  # Проверяем, что результат отсутствует
                return "[ERROR: Ошибка в выражении]"
            return result['UNIT_NAME']

    def get_unit_product_Xline(self, par_id):
        query = f"""
                    SELECT u.UNIT_NAME
                    FROM dbo.Units u
                    WHERE u.UNIT_ID = (
                    SELECT xc.UNIT
                    FROM dbo.Xline_config xc
                    WHERE xc.PAR_ID = %s
                    )
                """
        with self.connection.cursor() as cursor:
            cursor.execute(query, (par_id,))
            result = cursor.fetchone()  # Используем fetchone для одного результата
            if result is None:  # Проверяем, что результат отсутствует
                return "[ERROR: Ошибка в выражении]"
            return result['UNIT_NAME']
