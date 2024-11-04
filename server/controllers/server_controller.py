# server/controller/server_controller.py
import datetime
import json
import zlib

from server.models.db_model import DBModel
# Создаем экземпляр
db_model = DBModel()

def send_response_to_client(client_socket, response_data):
    """Отправляет сжатый ответ клиенту."""
    try:
        # Конвертируем данные в JSON и затем сжимаем их
        json_data = json.dumps(response_data).encode('utf-8')
        compressed_data = zlib.compress(json_data)

        # Отправляем данные клиенту
        client_socket.sendall(compressed_data)
    except Exception as e:
        print(f"Ошибка отправки данных клиенту: {e}")

def receive_request_from_client(client_socket):
    """Получает сжатый запрос от клиента и распаковывает его."""
    try:
        # Получаем сжатые данные от клиента
        compressed_request = client_socket.recv(8192)
        # Декомпрессия и декодирование данных
        request = json.loads(zlib.decompress(compressed_request).decode('utf-8'))
        return request
    except Exception as e:
        print(f"Ошибка получения данных от клиента: {e}")
        return None

def handle_client(client_socket):
    try:
        request = receive_request_from_client(client_socket)
        if not request:
            return
        print(f"Received request: {request}")  # Лог для отладки

        # Проверка, является ли request словарем
        if isinstance(request, dict):
            request_type = request.get("type", "")
            data = request.get("data", "")

            if request_type == "LOGIN":
                # Извлекаем имя пользователя и пароль из данных
                username = data.get("username")
                password = data.get("password")

                if not username or not password:
                    response_data = {"status": "error", "message": "Missing credentials"}
                else:
                    user = db_model.get_user_by_credentials(username, password)
                    if user:
                        response_data = {
                            "status": "success",
                            "role": user['role'].strip(),
                            "name": user['name'].strip()
                        }
                    else:
                        response_data = {"status": "error", "message": "Invalid credentials"}

                send_response_to_client(client_socket, response_data)


            elif request_type == "GET_TEMPLATE_NAMES":
                template_names = db_model.get_template_names()
                response_data = {
                    "status": "success",
                    "template_names": template_names
                } if template_names else {"status": "error", "message": "No templates found"}
                send_response_to_client(client_socket, response_data)


            elif request_type == "GET_TEMPLATE_DATA":
                template_name = data
                template_info = db_model.get_template_info(template_name)
                if template_info:
                    row_count, col_count, background_color, cells_data = template_info
                    response_data = {
                        "row_count": row_count,
                        "col_count": col_count,
                        "background_color": background_color,
                        "cells": cells_data
                    }
                else:
                    response_data = {"status": "error", "message": "Template not found"}
                send_response_to_client(client_socket, response_data)


            elif request_type == "SAVE_TEMPLATE":
                print(f"Processing SAVE_TEMPLATE for: {data}")
                template_name = data.get("template_name")
                row_count = data.get("row_count")
                col_count = data.get("col_count")
                cell_data = data.get("cell_data")
                creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
                success = db_model.save_template(template_name, row_count, col_count, cell_data, creation_date,
                                                 background_color="white")
                response_data = {"status": "success"} if success else {"status": "failure"}
                print(f"Sending response: {response_data}")  # Лог для отладки
                send_response_to_client(client_socket, response_data)


            elif request_type == "CHECK_TEMPLATE_EXISTS":
                template_name = data.get("template_name")
                template_exists = db_model.template_exists(template_name)
                response_data = {"status": "exists"} if template_exists else {"status": "not_exists"}
                send_response_to_client(client_socket, response_data)


            elif request_type == "UPDATE_TEMPLATE":
                template_name = data.get("template_name")
                row_count = data.get("row_count")
                col_count = data.get("col_count")
                cell_data = data.get("cell_data")
                creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
                success = db_model.update_template(template_name, row_count, col_count, cell_data, creation_date,
                                                   background_color="white")
                response_data = {"status": "success"} if success else {"status": "failure"}
                send_response_to_client(client_socket, response_data)


            elif request_type == "DELETE_TEMPLATE":
                template_name = data
                success = db_model.delete_template(template_name)
                response_data = {"status": "success"} if success else {"status": "failure"}
                send_response_to_client(client_socket, response_data)
        else:
                send_response_to_client(client_socket, {"status": "error", "message": "Invalid request format"})

    except Exception as e:
        # Обработка ошибки при обработке запроса
        print(f"Ошибка обработки запроса: {e}")
    finally:
        client_socket.close()

# Вспомогательная функция для форматирования данных шаблона
def format_template_data(template_data):
    # Преобразуем данные в строку, чтобы отправить их клиенту
    formatted_data = ""
    for row in template_data:
        formatted_data += ",".join(str(value) for value in row.values()) + "\n"
    return formatted_data

def handle_load_template_request(self, client_socket, template_id):
    template_data = self.database_service.load_template_cells(template_id)
    response_data = json.dumps(template_data)
    client_socket.sendall(response_data.encode('utf-8'))
