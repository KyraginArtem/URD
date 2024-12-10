# server/controller/server_controller.py
import datetime
import json
import zlib
from server.models.template_db_model import TemplateDBModel
from server.services.template_database_service import TemplateDatabaseService


class ServerController:
    def __init__(self):
        self.template_db_model = TemplateDBModel()
        self.service_db = TemplateDatabaseService()

    def send_response_to_client(self, client_socket, response_data):
        """Отправляет сжатый ответ клиенту."""
        try:
            json_data = json.dumps(response_data, ensure_ascii=False).encode("utf-8")
            compressed_data = zlib.compress(json_data)
            client_socket.sendall(compressed_data)
        except Exception as e:
            print(f"Ошибка отправки данных клиенту: {e}")

    def receive_request_from_client(self, client_socket):
        """Получает сжатый запрос от клиента и распаковывает его."""
        try:
            compressed_request = client_socket.recv(8192)
            request = json.loads(zlib.decompress(compressed_request).decode("utf-8"))
            return request
        except Exception as e:
            print(f"Ошибка получения данных от клиента: {e}")
            return None

    def handle_client(self, client_socket):
        """Обрабатывает запрос от клиента."""
        try:
            request = self.receive_request_from_client(client_socket)
            if not request:
                return
            print(f"Received request: {request}")

            if isinstance(request, dict):
                request_type = request.get("type", "")
                data = request.get("data", "")

                handlers = {
                    "LOGIN": self.handle_login,
                    "GET_TEMPLATE_NAMES": self.handle_get_template_names,
                    "GET_TEMPLATE_DATA": self.handle_get_template_data,
                    "SAVE_TEMPLATE": self.handle_save_template,
                    "CHECK_TEMPLATE_EXISTS": self.handle_check_template_exists,
                    "UPDATE_TEMPLATE": self.handle_update_template,
                    "DELETE_TEMPLATE": self.handle_delete_template,
                    "PARSE_CELL": self.handle_parse_cell,
                }

                handler = handlers.get(request_type)
                if handler:
                    handler(client_socket, data)
                else:
                    self.send_response_to_client(
                        client_socket,
                        {"status": "error", "message": "Unknown request type"},
                    )
            else:
                self.send_response_to_client(
                    client_socket,
                    {"status": "error", "message": "Invalid request format"},
                )
        except Exception as e:
            print(f"Ошибка обработки запроса: {e}")
        finally:
            client_socket.close()

    def handle_login(self, client_socket, data):
        """Обрабатывает запрос на вход в систему."""
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            response_data = {"status": "error", "message": "Missing credentials"}
        else:
            user = self.template_db_model.get_user_by_credentials(username, password)
            response_data = (
                {"status": "success", "role": user["role"].strip(), "name": user["name"].strip()}
                if user
                else {"status": "error", "message": "Invalid credentials"}
            )
        self.send_response_to_client(client_socket, response_data)

    def handle_get_template_names(self, client_socket, _):
        """Обрабатывает запрос на получение имен шаблонов."""
        template_names = self.template_db_model.get_template_names()
        response_data = (
            {"status": "success", "template_names": template_names}
            if template_names
            else {"status": "error", "message": "No templates found"}
        )
        self.send_response_to_client(client_socket, response_data)

    def handle_get_template_data(self, client_socket, template_name):
        """Обрабатывает запрос на получение данных шаблона."""
        template_info = self.template_db_model.get_template_info(template_name)
        if template_info:
            row_count, col_count, background_color, cells_data = template_info
            response_data = {
                "row_count": row_count,
                "col_count": col_count,
                "background_color": background_color,
                "cells": cells_data,
            }
        else:
            response_data = {"status": "error", "message": "Template not found"}
        self.send_response_to_client(client_socket, response_data)

    def handle_save_template(self, client_socket, data):
        """Обрабатывает запрос на сохранение шаблона."""
        template_name = data.get("template_name")
        row_count = data.get("row_count")
        col_count = data.get("col_count")
        cell_data = data.get("cell_data")
        background_color = data.get("background_color")
        creation_date = datetime.datetime.now().strftime("%Y-%m-%d")
        success = self.template_db_model.save_template(
            template_name, row_count, col_count, cell_data, creation_date, background_color
        )
        response_data = {"status": "success"} if success else {"status": "failure"}
        self.send_response_to_client(client_socket, response_data)

    def handle_check_template_exists(self, client_socket, data):
        """Обрабатывает запрос на проверку существования шаблона."""
        template_name = data.get("template_name")
        template_exists = self.template_db_model.template_exists(template_name)
        response_data = {"status": "exists"} if template_exists else {"status": "not_exists"}
        self.send_response_to_client(client_socket, response_data)

    def handle_update_template(self, client_socket, data):
        """Обрабатывает запрос на обновление шаблона."""
        template_name = data.get("template_name")
        row_count = data.get("row_count")
        col_count = data.get("col_count")
        cell_data = data.get("cell_data")
        background_color = data.get("background_color")
        creation_date = datetime.datetime.now().strftime("%Y-%m-%d")
        success = self.template_db_model.update_template(
            template_name, row_count, col_count, cell_data, creation_date, background_color
        )
        response_data = {"status": "success"} if success else {"status": "failure"}
        self.send_response_to_client(client_socket, response_data)

    def handle_delete_template(self, client_socket, template_name):
        """Обрабатывает запрос на удаление шаблона."""
        success = self.template_db_model.delete_template(template_name)
        response_data = {"status": "success"} if success else {"status": "failure"}
        self.send_response_to_client(client_socket, response_data)

    def handle_parse_cell(self, client_socket, cell_data):
        """
        Обрабатывает запрос на парсинг данных в ячейках.
        """
        result = {
            "cell_value": {}
        }

        # Проходим по каждой ячейке
        for cell_name, cell_expression in cell_data["cell_value"].items():
            # Используем сервис для обработки значения ячейки
            parsed_result = self.service_db.handle_parse(cell_expression, cell_data["start_time"],
                                                         cell_data["end_time"])

            # Если результат — это словарь, извлекаем значение по ключу
            if isinstance(parsed_result, dict):
                # Переходим к первому значению словаря
                key, value = next(iter(parsed_result.items()))
                parsed_result = value

                # Проверяем, является ли результат списком или одиночным значением
            if isinstance(parsed_result, list):
                if len(parsed_result) > 1:
                    # Если это список с несколькими значениями
                    result["cell_value"][cell_name] = {
                        "type": "list",
                        "value": parsed_result
                    }
                elif len(parsed_result) == 1:
                    # Если это список с одним значением
                    result["cell_value"][cell_name] = {
                        "type": "single",
                        "value": parsed_result[0]
                    }
                else:
                    # Пустой список
                    result["cell_value"][cell_name] = {
                        "type": "single",
                        "value": None
                    }
            else:
                # Если результат — одиночное значение
                result["cell_value"][cell_name] = {
                    "type": "single",
                    "value": parsed_result
                }
        # Формируем ответ
        response_data = result if result["cell_value"] else {"status": "error", "message": "No data parsed"}
        self.send_response_to_client(client_socket, response_data)

