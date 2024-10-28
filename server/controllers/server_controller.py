# server/controller/server_controller.py
import datetime
from server.models.db_model import DBModel
# Создаем экземпляр
db_model = DBModel()

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()

        if request.startswith("LOGIN"):
            _, username, password = request.split()
            user = db_model.get_user_by_credentials(username, password)
            if user:
                client_socket.send(f"Login successful|{user['role'].strip()}|{user['name'].strip()}".encode('utf-8'))
            else:
                client_socket.send("Invalid credentials".encode('utf-8'))

        elif request.startswith("GET_TEMPLATE_NAMES"):
            template_names = db_model.get_template_names()
            if template_names:
                response = ",".join(template_names)
                print(f"Отправленные шаблоны: {response}")  # Отладочное сообщение для проверки
                client_socket.send(response.encode('utf-8'))
            else:
                client_socket.send("No templates found".encode('utf-8'))

        elif request.startswith("GET_TEMPLATE_DATA"):
            _, template_name = request.split(maxsplit=1)
            template_info = db_model.get_template_info(template_name)
            if template_info:
                row_count, col_count, background_color, cell_data = template_info
                response = f"{row_count}|{col_count}|{background_color}|{cell_data}"
                client_socket.send(response.encode('utf-8'))
            else:
                client_socket.send("Template not found".encode('utf-8'))

        elif request.startswith("SAVE_TEMPLATE"):
            # Извлекаем данные шаблона из запроса
            _, template_name, row_count, col_count, cell_data = request.split("|", 4)
            # Сохраняем шаблон в базе данных
            creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
            success = db_model.save_template(template_name, int(row_count),
                                             int(col_count), cell_data, creation_date, background_color = "white")
            print(f"{success} ответ от БД в сервер контроллер")
            # Отправляем ответ клиенту в зависимости от успеха операции
            if success:
                response = "Template saved successfully"
            else:
                response = "Failed to save template"
            client_socket.send(response.encode('utf-8'))

        elif request.startswith("CHECK_TEMPLATE_EXISTS"):
            _, template_name = request.split(maxsplit=1)
            template_exists = db_model.template_exists(template_name)
            if template_exists:
                client_socket.send("Template exists".encode('utf-8'))
            else:
                client_socket.send("Template does not exist".encode('utf-8'))

        elif request.startswith("UPDATE_TEMPLATE"):
            _, template_name, row_count, col_count, cell_data = request.split("|", 4)
            # Сохраняем шаблон в базе данных
            creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
            success = db_model.update_template(template_name, int(row_count),
                                             int(col_count), cell_data, creation_date, background_color="white")
            print(f"{success} ответ от БД в сервер контроллер")
            # Отправляем ответ клиенту в зависимости от успеха операции
            if success:
                response = "Template update successfully"
            else:
                response = "Failed to update template"
            client_socket.send(response.encode('utf-8'))

        elif request.startswith("DELETE_TEMPLATE"):
            _, template_name = request.split("|", 1)
            success = db_model.delete_template(template_name)
            response = "Delete successful" if success else "Failed to delete template"
            client_socket.send(response.encode())

    except Exception as e:
        # Обработка ошибки при обработке запроса
        print(f"Ошибка обработки запроса: {e}")
    finally:
        # Закрываем сокет клиента
        client_socket.close()

# Вспомогательная функция для форматирования данных шаблона
def format_template_data(template_data):
    # Преобразуем данные в строку, чтобы отправить их клиенту
    formatted_data = ""
    for row in template_data:
        formatted_data += ",".join(str(value) for value in row.values()) + "\n"
    return formatted_data
