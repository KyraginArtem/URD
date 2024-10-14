from server.models.db_model import DBModel

# Создаем экземпляр модели для работы с базой данных
db_model = DBModel()

# Функция для обработки клиента
def handle_client(client_socket):
    try:
        # Читаем запрос от клиента
        request = client_socket.recv(1024).decode()
        # Проверяем, является ли запрос командой LOGIN
        if request.startswith("LOGIN"):
            # Извлекаем имя пользователя и пароль из запроса
            _, username, password = request.split()
            # Проверяем учетные данные с помощью модели
            user = db_model.get_user_by_credentials(username, password)
            # Отправляем результат проверки обратно клиенту
            if user:
                client_socket.send("Login successful".encode())
            else:
                client_socket.send("Invalid credentials".encode())
    except Exception as e:
        # Обработка ошибки при обработке запроса
        print(f"Ошибка обработки запроса: {e}")
    finally:
        # Закрываем сокет клиента
        client_socket.close()
